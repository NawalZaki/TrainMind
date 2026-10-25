# TrainMind — ITI Trainer Copilot

TrainMind creates a complete training package from uploaded curriculum PDFs:

- Beginner, Intermediate, and Advanced levels
- A quiz, practical exercise, and 90-minute session plan for each level
- PDF, PowerPoint (`.pptx`), and Word (`.docx`) exports
- Local persistent ChromaDB index; newly uploaded or changed PDFs are indexed automatically

## Model setup

- **Generation:** Gemini API (`GEMINI_MODEL`, default `gemini-2.5-flash`)
- **Embeddings:** local Ollama model `nomic-embed-text`
- **Vector database:** ChromaDB, stored under `data/chroma`

Gemini Free Tier quotas vary by account, region, and current model availability. TrainMind makes one Gemini generation request per package, but the full package is a larger request than a single answer. If the configured model is unavailable in your account, set `GEMINI_MODEL` in `.env` to a model listed in Google AI Studio for your key.

## Windows setup (PowerShell)

Run these commands from the project folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
ollama pull nomic-embed-text
```

If you already have a `.venv`, activate it instead of creating it again.

Create a local `.env` file beside `home.py` using `.env.example` as a template, then paste your own Gemini API key:

```dotenv
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_OUTPUT_TOKENS=12000
```

Do not share or upload `.env`.

Make sure Ollama is running, then start the app:

```powershell
streamlit run home.py
```

## How to use

1. Upload one or more curriculum PDFs. TrainMind extracts and indexes new/changed files automatically.
2. Enter a topic that appears in the uploaded material.
3. Click **Generate Package** once.
4. Review the nine artifacts in the level tabs.
5. Download the complete package as PDF, PowerPoint, or Word.

Previously indexed files remain in `data/chroma`, so you do not need to upload or index the same unchanged file every time. To start from a clean index, stop the app and back up/delete `data/chroma` before launching again.

## Important grounding behavior

TrainMind uses retrieved passages from the uploaded curriculum. If a task is not supported by those passages, the generated artifact should explain the limitation rather than inventing content. The app displays the retrieved source filenames and pages with the package. As with any generative system, review the content before delivering it to trainees.

## Tests

Syntax-check the project:

```powershell
python -m compileall app home.py
```

Run the offline unit tests after installing dependencies:

```powershell
python -m pytest test_agent_routing.py test_agent_logic.py test_revision_loop.py test_validation_graph.py test_quiz_tool.py -q
```

Some legacy manual test scripts query local Ollama/ChromaDB or call external services, so they may require a running Ollama instance and a populated local index.
