import random
import re


# Списки для безопасной подстановки
ADJECTIVE_WORDS = {
    "big",
    "small",
    "red",
    "blue",
    "green",
    "yellow",
    "black",
    "brown",
    "white",
    "happy",
    "sad",
    "nice",
    "lovely",
    "wonderful",
    "funny",
    "pretty",
    "cute",
    "different",
    "hot",
    "cold",
    "windy",
    "sunny",
    "raining",
}

VERB_WORDS = {
    "see",
    "look",
    "look at",
    "play",
    "put on",
    "take off",
    "wear",
    "eat",
    "drink",
    "sing",
    "swim",
    "run",
    "jump",
    "climb",
    "fly",
    "dance",
    "help",
    "like",
    "want",
    "have fun",
    "make",
}

FUNCTION_WORDS = {
    "in",
    "on",
    "under",
    "at",
    "to",
    "from",
    "it",
    "he",
    "she",
    "you",
    "we",
    "they",
    "our",
    "your",
    "his",
    "her",
    "their",
    "them",
    "this",
    "that",
    "these",
    "those",
    "yes",
    "no",
    "too",
    "very",
}

NOUN_TEMPLATES = [
    'Посмотри на картинку. Укажи на {word} и скажи: "This is my {word}."',
    'Поиграй с другом. Спроси: "Do you have a {word}?" Он/она отвечает: "Yes, I do / No, I don\'t".',
    'Покажи {word} другу. Скажи: "I like my {word}." Потом спроси: "And you?"',
    'Укажи на {word}. Скажи: "I see {word}."',
]

ADJ_TEMPLATES = [
    'Посмотри на картинку. Скажи: "It is {word}." Спроси друга: "Is it {word}?"',
    'Покажи предмет и скажи: "It is {word}." Друг отвечает: "Yes, it is / No, it isn\'t".',
    'Скажи 2 предложения: "It is {word}. I like it."',
]

QUESTION_TEMPLATES = [
    'Поиграй с другом. Спроси: "{word}" Друг отвечает коротко.',
    'Скажи: "{word}" и попроси друга ответить.',
    'Поменяйтесь ролями: ты спрашиваешь "{word}", друг отвечает.',
]

FALLBACK_TEMPLATES = [
    'Скажи слово/фразу: "{word}". Попроси друга повторить.',
    'Произнеси: "{word}". Затем спроси друга: "Can you say it?"',
]


def generate_exercises_local(count: int, vocab_words: list[str]) -> str:
    """Локальная генерация упражнений без внешнего API."""
    if not vocab_words:
        vocab_words = ["toy", "ball", "teddy bear"]

    noun_words, adj_words, question_words, other_words = _categorize_words(vocab_words)
    lines = []

    for i in range(count):
        kind, word = _pick_word(noun_words, adj_words, question_words, other_words, vocab_words)
        template = _pick_template(kind)
        text = template.format(word=word)
        lines.append(f"{i + 1}. {text}")

    return "\n".join(lines)


def _categorize_words(words: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    noun_words: list[str] = []
    adj_words: list[str] = []
    question_words: list[str] = []
    other_words: list[str] = []

    for raw in words:
        word = raw.strip()
        if not word:
            continue
        low = word.lower()

        if "?" in word:
            question_words.append(word)
            continue
        if low in ADJECTIVE_WORDS:
            adj_words.append(word)
            continue
        if low in VERB_WORDS or low in FUNCTION_WORDS:
            other_words.append(word)
            continue
        if re.search(r"[!?.]", word):
            other_words.append(word)
            continue

        noun_words.append(word)

    return noun_words, adj_words, question_words, other_words


def _pick_word(
    noun_words: list[str],
    adj_words: list[str],
    question_words: list[str],
    other_words: list[str],
    fallback: list[str],
) -> tuple[str, str]:
    choices = []
    if noun_words:
        choices.append(("noun", noun_words))
    if adj_words:
        choices.append(("adj", adj_words))
    if question_words:
        choices.append(("question", question_words))

    if not choices:
        # Если нет "безопасных" слов, используем всё подряд
        if other_words:
            return "fallback", random.choice(other_words)
        return "fallback", random.choice(fallback)

    kind, words = random.choice(choices)
    return kind, random.choice(words)


def _pick_template(kind: str) -> str:
    if kind == "adj":
        return random.choice(ADJ_TEMPLATES)
    if kind == "question":
        return random.choice(QUESTION_TEMPLATES)
    if kind == "fallback":
        return random.choice(FALLBACK_TEMPLATES)
    return random.choice(NOUN_TEMPLATES)
