# Exercise Balancer Bot (Spotlight 2)

Telegram-бот на aiogram 3.x для балансировки упражнений в учебнике Spotlight 2.
Работает в 3 шага:
1) Загрузи CSV с упражнениями.
2) Загрузи TXT с вокабуляром по юнитам.
3) Команда /generate — добавляет коммуникативные упражнения для баланса 50/50 (или выше).

## Возможности
- Анализ CSV (количество и доля коммуникативных/языковых).
- Генерация коммуникативных упражнений по вокабуляру юнитов.
- Выгрузка 2 файлов: полный датасет и только сгенерированные упражнения.

## Требования
- Python 3.10+
- Telegram Bot Token

## Установка
```bash
pip install -r requirements.txt
```

## Настройка окружения
Создай файл `.env` в корне проекта (рядом с `bot.py`) и укажи токен:
```
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
LLM_PROVIDER=local
```

Опционально можно использовать локальный Ollama:
```
LLM_PROVIDER=ollama
OLLAMA_ENDPOINT=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:7b-instruct
```

## Запуск
```bash
python bot.py
```

## Форматы файлов

CSV:
```
instruction,page_num,pred_label
Слушай и повторяй...,5,linguistic
Поговори с другом...,6,communicative
```

TXT (вокабуляр, пример):
```
Module 1
Unit 1: My Home!
bed /bed/ кровать
chair /tʃeər/ стул
```

## Команды бота
- /start — инструкция
- /generate — генерация упражнений

## Безопасность
Файл `.env` исключён из Git (см. `.gitignore`).
