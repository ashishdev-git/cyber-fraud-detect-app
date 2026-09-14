# CyberShield

Local fraud-assessment demo using Gemini, FastAPI, LangGraph, and Streamlit.

## Run

Set GOOGLE_API_KEY in .env. Keep that file private. No other API key is needed.
Streamlit calls shared Python functions directly; a FastAPI server is optional.
To use the optional REST API, run:

```sh
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```sh
.venv/bin/python -m streamlit run client.py --server.address 127.0.0.1
```

Open http://localhost:8501. Restart both processes after code changes.

## Features

- Five sample-message buttons, including Hindi, Hinglish, and a legitimate message.
- Colour-coded risk levels with indicators and recommendations; the uncalibrated model probability is not shown.
- English, Hindi, or Hinglish analysis output (UI labels are English).
- PNG, JPEG, and WebP screenshots up to 5 MB and 20 megapixels; screenshots can be submitted without a message. Images are validated, resized, and sent to Gemini. Extracted text is shown.
- Gemini URL assessment and offline URL-pattern inspection. No URLs are opened, redirects followed, or live reputation lists queried. No claim of website safety is made. Up to ten URLs beginning with http://, https://, or www. are inspected, including URLs transcribed from screenshots.
- Helpful/not-helpful feedback, saved in data/feedback.sqlite3. Repeated feedback updates the same assessment's rating. Only random IDs, risk labels, ratings, and timestamps are stored; original text and screenshots are not saved locally.

Remove sensitive details before submitting. Gemini receives the supplied text and image.
This is a local demo. Results depend on available evidence and may be wrong.

## Configuration and checks

Optional GEMINI_MODEL selects a different model available to your Gemini account.
Optional CYBERSHIELD_DB changes the local database path.
The frontend does not require CYBERSHIELD_API_URL or a running backend.

## Streamlit Community Cloud

Deploy client.py from the repository. In App settings > Secrets, configure:

```toml
GOOGLE_API_KEY = "your_actual_key"
```

Keep the key out of GitHub. Root-level Streamlit secrets are exposed as environment variables.
Push all code changes, including app/service.py, to the branch used by Streamlit.
Reboot the cloud app after updating secrets if needed.
Local SQLite feedback is temporary on cloud hosting and may be lost on rebuild.

Install dependencies with `.venv/bin/python -m pip install -r requirements.txt`.
Run offline checks with `.venv/bin/python -B -m unittest discover -s tests -v`.
Tests mock Gemini and use a temporary feedback database; they do not call external services.
