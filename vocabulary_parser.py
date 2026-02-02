import re


VOCAB_SECTION_PATTERNS = [
    re.compile(r"\bVOCABULARY\b", re.IGNORECASE),
    re.compile(r"\bWORD\s+LIST\b", re.IGNORECASE),
]


def _find_vocab_section(text: str) -> str:
    """Ищем начало раздела вокабуляра и возвращаем текст с этого места."""
    for pattern in VOCAB_SECTION_PATTERNS:
        match = None
        for m in pattern.finditer(text):
            match = m
        if match:
            return text[match.start():]
    return ""


def parse_vocabulary(text: str) -> dict:
    """
    Парсим вокабуляр по Unit/Module.
    Возвращаем структуру:
    {
        "units": { "UNIT 1": { "Module 1": [..], ... }, ... },
        "unit_words": { "UNIT 1": [..], ... },
        "order_units": ["UNIT 1", ...],
        "order_modules": ["Module 1", ...]
    }
    """
    section = _find_vocab_section(text) or text

    unit_re = re.compile(r"^\s*UNIT\s+(\d+)\b", re.IGNORECASE)
    unit_title_re = re.compile(r"^\s*Unit\s+(\d+)\b", re.IGNORECASE)
    module_re = re.compile(r"^\s*Module\s+([0-9]+[a-z]?)\b", re.IGNORECASE)
    page_marker_re = re.compile(r"^\s*-{2,}\s*PAGE\s+\d+\s*-{2,}\s*$", re.IGNORECASE)

    units: dict[str, dict[str, list[str]]] = {}
    unit_words: dict[str, list[str]] = {}
    order_units: list[str] = []
    order_modules: list[str] = []

    current_unit = None
    current_module = None

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if page_marker_re.match(line):
            continue

        unit_match = unit_re.match(line) or unit_title_re.match(line)
        if unit_match:
            unit_num = unit_match.group(1)
            current_unit = f"UNIT {unit_num}"
            units.setdefault(current_unit, {})
            unit_words.setdefault(current_unit, [])
            if current_unit not in order_units:
                order_units.append(current_unit)
            continue

        module_match = module_re.match(line)
        if module_match:
            module_code = module_match.group(1)
            current_module = f"Module {module_code}"
            if current_module not in order_modules:
                order_modules.append(current_module)
            if current_unit:
                units[current_unit].setdefault(current_module, [])
            continue

        word = _extract_word_from_line(line)
        if word and current_unit:
            unit_words.setdefault(current_unit, []).append(word)
            if current_module:
                units[current_unit].setdefault(current_module, []).append(word)

    if not unit_words:
        raise ValueError("Не удалось распознать юниты и слова в файле вокабуляра.")

    return {
        "units": units,
        "unit_words": unit_words,
        "order_units": order_units,
        "order_modules": order_modules,
    }


def get_words_for_unit(vocab: dict, unit: str) -> list[str]:
    """Получаем слова для конкретного юнита."""
    return vocab.get("unit_words", {}).get(unit, [])


def get_all_words(vocab: dict, limit: int | None = None) -> list[str]:
    """Собираем все слова."""
    all_words: list[str] = []
    for words in vocab.get("unit_words", {}).values():
        all_words.extend(words)
    if limit:
        return all_words[:limit]
    return all_words


def _extract_word_from_line(line: str) -> str | None:
    """Извлекаем слово/фразу из строки вида 'word /phonetic/ translation'."""
    lowered = line.lower()
    if lowered.startswith(("unit ", "module ", "spotlight", "the town mouse")):
        return None
    if line.startswith("-"):
        return None
    if "/" not in line:
        return None
    match = re.match(r"^(.*?)\s*/", line)
    if not match:
        return None
    word = match.group(1).strip()
    if not word:
        return None
    return word
