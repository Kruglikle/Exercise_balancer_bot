# Exercise Balancer Bot

Telegram bot based on aiogram 3 for generating URU (lesson exercise sets) for Spotlight 2.

## Features
- Generates a complete URU set from text input (no file upload required).
- Supports two workflows:
  - `/generate` for step-by-step input.
  - `/generate_one` for one-message input.
- Sends output in chat and as a `.docx` file.
- Saves generated documents to `generated_documents/`.
- Supports multiple LLM providers: `openrouter`, `qwen`, `ollama`, `local`.
- Uses editable prompt template from `PROMPT.md`.
- Can send local Spotlight 2 student/teacher PDFs from the start menu.

## Requirements
- Python 3.10+
- Telegram bot token
- Optional: OpenRouter API key, DashScope (Qwen) API key, or local Ollama

## Installation
```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration
Create `.env` in the project root (or copy from `.env.example`).

Minimum required:
```env
BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
```

### Provider options

OpenRouter:
```env
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=YOUR_OPENROUTER_KEY
OPENROUTER_MODEL=YOUR_OPENROUTER_MODEL
OPENROUTER_ENDPOINT=https://openrouter.ai/api/v1/chat/completions
OPENROUTER_REFERER=
OPENROUTER_TITLE=
```

DashScope Qwen:
```env
LLM_PROVIDER=qwen
QWEN_API_KEY=YOUR_DASHSCOPE_KEY
```

Ollama:
```env
LLM_PROVIDER=ollama
OLLAMA_ENDPOINT=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:7b-instruct
```

Local fallback (no external API):
```env
LLM_PROVIDER=local
```

If `LLM_PROVIDER` is empty, the bot selects provider automatically:
1. `openrouter` if `OPENROUTER_API_KEY` is present.
2. `qwen` if `QWEN_API_KEY` is present.
3. `local` fallback otherwise.

## Run
```bash
python bot.py
```

## Bot Commands
- `/start` - welcome message and action buttons.
- `/help` - usage help.
- `/generate` - guided multi-step generation flow.
- `/generate_one` - one-message generation flow.
- `/show_prompt` - show and send current `PROMPT.md`.
- `/cancel` - cancel current input flow.

## Input format for `/generate_one`
Send all fields in one message. Example:

```text
Unit: Unit 3a
New vocabulary/grammar:
clothes: jacket, shoes, dress
have got / has got
Old support material:
colors, is it ... ?
```

Required fields:
- `Unit`
- `New vocabulary/grammar`

Optional fields:
- `Old support material` (you can pass `-` or `none`)

## Output
- Generated URU text in Telegram messages.
- Generated `.docx` file sent back to user.
- Local `.docx` copy in `generated_documents/`.

## Optional local materials
If these files are placed in the project root, the bot can send them from `/start`:
- Teacher book PDF (file name contains `teacher` and `book`).
- Student book PDF (file name contains `student` and `book`).

## Project Structure
- `bot.py` - Telegram handlers, input parsing, docx export.
- `llm_client.py` - provider selection and unified generation API.
- `openrouter_client.py` - OpenRouter integration.
- `qwen_client.py` - DashScope Qwen integration.
- `ollama_client.py` - Ollama integration.
- `local_generator.py` - local template fallback.
- `PROMPT.md` - generation prompt template.

## Security
- `.env` is ignored by git.
- Do not commit real API keys or bot tokens.
