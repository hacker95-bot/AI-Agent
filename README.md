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
 
5. (Optional) Expose the server to the internet with [ngrok](https://ngrok.com/)
   1. Install and authenticate ngrok (`ngrok config add-authtoken <token>`)
   2. Start the server and tunnel
      ```bash
      ./scripts/run_ngrok.sh
      ```
   3. Copy the HTTPS "Forwarding" URL printed by ngrok and configure your WhatsApp Cloud API app to use `<forwarding-url>/wa/webhook`.

## Testing

Run the unit tests with
```bash
pytest
```
