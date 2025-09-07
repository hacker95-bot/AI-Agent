# WhatsApp RAG Bot

Minimal prototype of a Retrieval-Augmented Generation (RAG) chatbot for WhatsApp based on the plan in `whatsapp_bot_plan.md`.

## Setup

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and fill in your tokens.
3. Add files to `admin/kb/` and build the knowledge base
   ```bash
   python admin/ingest.py
   ```
4. Run the server
   ```bash
   ./scripts/run_local.sh
   ```
5. Configure your WhatsApp Cloud API app to point to `http://<host>:8000/wa/webhook`.

## Testing

Run the unit tests with
```bash
pytest
```
