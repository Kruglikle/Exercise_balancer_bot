import asyncio
import csv
from io import BytesIO, StringIO
from typing import List

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BufferedInputFile, Message

from analyzer import analyze_exercises, calc_needed_total, parse_csv_bytes
from config import BOT_TOKEN, TARGET_COMMUNICATIVE_RATIO
from llm_client import LLMError, generate_exercises
from vocabulary_parser import get_all_words, get_words_for_unit, parse_vocabulary


def _decode_bytes(raw: bytes) -> str:
    """Декодируем текстовые файлы с учётом типичных кодировок."""
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def format_stats(stats: dict) -> str:
    """Форматируем статистику для пользователя."""
    total = stats.get("total", 0)
    communicative = stats.get("communicative", 0)
    linguistic = stats.get("linguistic", 0)
    ratio = stats.get("ratio", 0.0) * 100
    diff = ratio - (TARGET_COMMUNICATIVE_RATIO * 100)
    if diff < 0:
        balance_note = f"Дисбаланс: не хватает коммуникативных (-{abs(diff):.1f}%)."
    elif diff > 0:
        balance_note = f"Дисбаланс: избыток коммуникативных (+{diff:.1f}%)."
    else:
        balance_note = "Баланс идеален (50/50)."

    return (
        f"Всего упражнений: {total}\n"
        f"Коммуникативных: {communicative}\n"
        f"Языковых: {linguistic}\n"
        f"Доля коммуникативных: {ratio:.1f}%\n"
        f"{balance_note}"
    )


def build_prompt(count: int, vocab_words: List[str]) -> str:
    """Формируем промпт для генерации."""
    vocab_str = ", ".join(vocab_words)
    return (
        "Ты опытный учитель английского языка для младших школьников. "
        f"Создай {count} коммуникативных упражнений для развития говорения у детей 7-8 лет (уровень Pre-A1).\n\n"
        f"ОБЯЗАТЕЛЬНАЯ ЛЕКСИКА: {vocab_str}\n\n"
        "ТРЕБОВАНИЯ:\n"
        "- Упражнения должны развивать ПРОДУКТИВНУЮ речь (не повторение и не аудирование)\n"
        '- Используй визуальные опоры: "Посмотри на картинку...", "Покажи...", "Укажи на..."\n'
        "- Фразы должны быть короткими: 35 слов максимум\n"
        '- Добавь игровые элементы: "Давай поиграем", "Угадай, что у меня", "Поиграй с другом"\n'
        "- Для каждого упражнения дай простой образец/стартер диалога\n"
        "- Избегай письменных заданий — фокус только на устной речи\n"
        "- Грамматика и лексика должны быть корректными\n"
        "- Обязательно используй слова из ОБЯЗАТЕЛЬНОЙ ЛЕКСИКИ\n"
        "- Каждое упражнение на отдельной строке, пронумеровано: 1., 2., 3.\n\n"
        "ПРИМЕР ФОРМАТА:\n"
        "1. Посмотри на картинку. Укажи на [игрушку] и скажи: \"I like my [teddy bear].\"\n"
        "2. Спроси друга: \"Do you have a [ball]?\" Он/она отвечает: \"Yes, I do / No, I don't\".\n"
        "3. Покажи свою любимую [игрушку] другу. Скажи 2 предложения: \"This is my... It is [big/small/red].\""
    )


def parse_generated_lines(text: str) -> List[str]:
    """Разбираем ответ модели на список упражнений."""
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = line.lstrip("0123456789.-) ")
        if line:
            lines.append(line)
    return lines


def build_csv_bytes(rows: list[dict]) -> bytes:
    """Собираем CSV из списка словарей."""
    output = StringIO()
    has_unit = any("unit" in r for r in rows)
    fieldnames = ["instruction", "page_num", "pred_label"]
    if has_unit:
        fieldnames.append("unit")
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return output.getvalue().encode("utf-8")


def distribute_needed_across_units(needed_total: int, units: list[str]) -> dict:
    """Распределяем нужное количество упражнений по юнитам без ограничения 1-3."""
    if needed_total <= 0 or not units:
        return {}

    plan = {u: 0 for u in units}
    idx = 0
    remaining = needed_total

    while remaining > 0:
        unit = units[idx % len(units)]
        plan[unit] += 1
        remaining -= 1
        idx += 1

    return {u: c for u, c in plan.items() if c > 0}


async def download_document_bytes(bot: Bot, message: Message) -> bytes:
    """Скачиваем файл из Telegram в память."""
    document = message.document
    if not document:
        raise ValueError("Файл не найден в сообщении.")

    file = await bot.get_file(document.file_id)
    buffer = BytesIO()
    if hasattr(bot, "download_file"):
        await bot.download_file(file.file_path, destination=buffer)
    else:
        await bot.download(file, destination=buffer)
    return buffer.getvalue()


async def on_start(message: Message):
    await message.answer(
        "Привет! Я помогу сбалансировать упражнения в Spotlight 2.\n"
        "Шаги:\n"
        "1) Отправь CSV с упражнениями (instruction, page_num, pred_label).\n"
        "2) Отправь TXT с вокабуляром по юнитам.\n"
        "3) Команда /generate — сгенерировать коммуникативные упражнения и получить 2 таблицы.\n\n"
        "Команда:\n"
        "/generate — генерация упражнений"
    )


async def on_help(message: Message):
    await message.answer(
        "Инструкция:\n"
        "1) Загрузи CSV с упражнениями.\n"
        "2) Загрузи TXT с вокабуляром (Unit/Module + слова).\n"
        "3) Используй /generate для добавления коммуникативных упражнений.\n\n"
        "Цель: приблизиться к балансу 50/50 (может быть 60-70% коммуникативных)."
    )


async def on_generate(message: Message, state: FSMContext):
    data = await state.get_data()
    rows = data.get("csv_rows")
    vocab = data.get("vocab")

    if not rows:
        await message.answer("Сначала загрузите CSV файл.")
        return
    if not vocab:
        await message.answer("Сначала загрузите TXT с вокабуляром.")
        return

    stats_before = analyze_exercises(rows)
    needed_total = calc_needed_total(stats_before, TARGET_COMMUNICATIVE_RATIO)
    if needed_total <= 0:
        await message.answer("Коммуникативных упражнений достаточно. Генерация не требуется.")
        return

    units_order = vocab.get("order_units", [])
    if not units_order:
        await message.answer("Не удалось найти юниты в вокабуляре. Проверьте формат TXT.")
        return

    plan = distribute_needed_across_units(needed_total, units_order)
    if not plan:
        await message.answer("Не удалось распределить задания по юнитам.")
        return

    plan_text = "\n".join([f"{unit}: {count}" for unit, count in plan.items()])
    await message.answer(
        "План генерации (по юнитам):\n" + plan_text
    )

    new_rows = list(rows)
    generated_rows: list[dict] = []
    for unit, count in plan.items():
        words = get_words_for_unit(vocab, unit)
        if not words:
            words = get_all_words(vocab, limit=30)

        prompt = build_prompt(count, words)
        await message.answer(f"Генерирую упражнения для {unit}...")

        try:
            generated_text = await generate_exercises(prompt, count, words)
        except LLMError as exc:
            await message.answer(f"Ошибка генерации для {unit}: {exc}")
            continue

        lines = parse_generated_lines(generated_text)
        if not lines:
            await message.answer(f"Модель не вернула упражнения для {unit}.")
            continue

        for line in lines[:count]:
            row = {
                "instruction": line,
                "page_num": "",
                "pred_label": "communicative",
                "unit": unit,
            }
            new_rows.append(row)
            generated_rows.append(row)

    stats_after = analyze_exercises(new_rows)
    csv_bytes = build_csv_bytes(new_rows)
    input_file = BufferedInputFile(csv_bytes, filename="balanced_exercises.csv")
    await message.answer_document(input_file)

    if generated_rows:
        gen_bytes = build_csv_bytes(generated_rows)
        gen_file = BufferedInputFile(gen_bytes, filename="generated_exercises.csv")
        await message.answer_document(gen_file)
    msg = (
        "Статистика до/после:\n\n"
        "До:\n"
        f"{format_stats(stats_before)}\n\n"
        "После:\n"
        f"{format_stats(stats_after)}"
    )
    await message.answer(msg)

    await state.update_data(csv_rows=new_rows, stats=stats_after)


async def on_document(message: Message, bot: Bot, state: FSMContext):
    document = message.document
    if not document:
        return

    filename = (document.file_name or "").lower()
    try:
        file_bytes = await download_document_bytes(bot, message)
    except Exception as exc:
        await message.answer(f"Не удалось скачать файл: {exc}")
        return

    if filename.endswith(".csv"):
        try:
            rows = parse_csv_bytes(file_bytes)
        except Exception as exc:
            await message.answer(f"Ошибка чтения CSV: {exc}")
            return
        await state.update_data(csv_rows=rows)
        stats = analyze_exercises(rows)
        await state.update_data(stats=stats)
        await message.answer("CSV файл загружен.\n" + format_stats(stats))
        return

    if filename.endswith(".txt"):
        text = _decode_bytes(file_bytes)
        try:
            vocab = parse_vocabulary(text)
        except Exception as exc:
            await message.answer(f"Ошибка парсинга вокабуляра: {exc}")
            return
        await state.update_data(vocab=vocab)
        units_count = len(vocab.get("order_units", []))
        await message.answer(f"TXT файл загружен. Найдено юнитов: {units_count}.")
        return

    await message.answer("Поддерживаются только файлы CSV и TXT.")


async def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN в переменных окружения.")

    bot = Bot(BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.register(on_start, Command("start"))
    dp.message.register(on_help, Command("help"))
    dp.message.register(on_generate, Command("generate"))
    dp.message.register(on_document, F.document)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
