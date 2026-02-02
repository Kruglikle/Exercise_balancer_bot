import csv
from io import StringIO
import math


def _decode_bytes(raw: bytes) -> str:
    """Пытаемся декодировать байты с учётом типичных кодировок."""
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    # Последняя попытка — с заменой символов
    return raw.decode("utf-8", errors="replace")


def normalize_label(label: str) -> str:
    """Нормализуем метку упражнения к каноническому виду."""
    if not label:
        return ""
    v = label.strip().lower()
    # Поддержка английских и русских меток
    if v in {"communicative", "коммуникативное", "коммуникативный"}:
        return "communicative"
    if v in {"linguistic", "языковое", "языковой"}:
        return "linguistic"
    return v


def parse_csv_bytes(raw: bytes) -> list[dict]:
    """Парсим CSV из bytes в список словарей."""
    text = _decode_bytes(raw)
    reader = csv.DictReader(StringIO(text))
    required = {"instruction", "page_num", "pred_label"}
    if not reader.fieldnames:
        raise ValueError("CSV пустой или не содержит заголовков.")
    missing = required - set(fn.strip() for fn in reader.fieldnames)
    if missing:
        raise ValueError(f"В CSV отсутствуют столбцы: {', '.join(sorted(missing))}")

    rows = []
    for row in reader:
        # Приводим ключи к ожидаемым
        norm_row = {
            "instruction": row.get("instruction", "").strip(),
            "page_num": row.get("page_num", "").strip(),
            "pred_label": normalize_label(row.get("pred_label", "")),
        }
        # Если есть дополнительные поля — сохраняем
        if "unit" in row:
            norm_row["unit"] = row.get("unit", "").strip()
        if "module" in row:
            norm_row["module"] = row.get("module", "").strip()
        rows.append(norm_row)
    return rows


def analyze_exercises(rows: list[dict]) -> dict:
    """Считаем общую статистику и статистику по страницам."""
    total = 0
    communicative = 0
    linguistic = 0
    per_page: dict[int, dict] = {}

    for row in rows:
        total += 1
        label = row.get("pred_label", "")
        if label == "communicative":
            communicative += 1
        elif label == "linguistic":
            linguistic += 1

        # Нормализация номера страницы
        page_raw = row.get("page_num", "")
        try:
            page = int(float(page_raw))
        except (ValueError, TypeError):
            # Если номер страницы некорректный, пропускаем пер-страничную статистику
            continue

        if page not in per_page:
            per_page[page] = {"total": 0, "communicative": 0, "linguistic": 0}
        per_page[page]["total"] += 1
        if label == "communicative":
            per_page[page]["communicative"] += 1
        elif label == "linguistic":
            per_page[page]["linguistic"] += 1

    ratio = (communicative / total) if total else 0.0
    return {
        "total": total,
        "communicative": communicative,
        "linguistic": linguistic,
        "ratio": ratio,
        "per_page": per_page,
    }


def calc_needed_per_page(per_page: dict[int, dict], target_ratio: float = 0.5) -> dict[int, int]:
    """Для каждой страницы считаем, сколько коммуникативных упражнений нужно добавить."""
    needed: dict[int, int] = {}
    for page, stats in per_page.items():
        total = stats.get("total", 0)
        communicative = stats.get("communicative", 0)
        if total == 0:
            continue
        # Минимальное x, чтобы (c + x) / (t + x) >= target_ratio
        # Для target_ratio = 0.5 формула упрощается до x >= t - 2c
        if target_ratio == 0.5:
            x = total - 2 * communicative
        else:
            x = int((target_ratio * total - communicative) / (1 - target_ratio))
        if x > 0:
            needed[page] = x
    return needed


def calc_needed_total(stats: dict, target_ratio: float = 0.5) -> int:
    """Считаем, сколько коммуникативных нужно добавить для достижения целевого баланса."""
    total = stats.get("total", 0)
    communicative = stats.get("communicative", 0)
    if total == 0:
        return 0
    if target_ratio >= 1:
        return 0
    if target_ratio == 0.5:
        needed = total - 2 * communicative
        return max(0, needed)

    needed = math.ceil((target_ratio * total - communicative) / (1 - target_ratio))
    return max(0, needed)
