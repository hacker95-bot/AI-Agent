# WhatsApp RAG Bot Development Plan

## 0) Constraints & Design Rules
- **Stateless**: do not persist user messages or identifiers. Log only minimal operational metrics (counts) with no PII.
- **RAG-only**: answer **only** from KB context; otherwise say “I don’t know based on the current knowledge base.”
- **Free-window ops**: never send outbound templates outside the 24h window; rely on user initiation.

## 1) System Architecture (Lean)
- **Transport (WhatsApp)**: Meta WhatsApp Business Cloud API → your webhook.
- **API/Webhook**: FastAPI (Python) or Fastify (Node) — stateless.
- **RAG engine**: Local embeddings + FAISS (on-disk index) + local LLM via **Ollama**.
- **Admin KB**: Files in `./kb/`; a one-click `ingest` script builds `index.faiss` + `chunks.jsonl`.
- **No DB**: Only artifacts saved are the **KB index** and **chunk metadata** (not chats).
- **Optional free prototype**: identical stack behind **Telegram** or a **web chat** (true $0).

## 2) Tech Stack (Minimal + Free)
- **Models (local)**:  
  - Embeddings: `nomic-embed-text` or `bge-m3` via Ollama  
  - LLM: `llama3.1:8b-instruct` or `phi3:mini` via Ollama
- **Vector store**: FAISS (file).
- **Parsing**: `unstructured` (for PDF/DOCX/HTML), `pdfminer.six` (PDF).
- **Server**: FastAPI + Uvicorn **or** Node + Fastify.
- **Infra**: local machine or free-tier VM. Containerize with Docker later.

## 3) Project Layout
```
whatsapp-rag-bot/
  app/
    main.py                  # webhook + /ask endpoint
    wa.py                    # WhatsApp signature verify + send helpers
    rag.py                   # search + prompt compose + LLM call
    config.py                # env (model names, top_k, timeouts)
  admin/
    ingest.py                # parse → chunk → embed → build FAISS index
    kb/                      # your source files
    chunks.jsonl             # text chunks + source (generated)
    index.faiss              # FAISS index (generated)
  tests/
    test_rag.py
    test_prompt.py
  scripts/
    run_local.sh
  .env.example
  README.md
```

## 4) Minimal Endpoints
- `POST /wa/webhook` — receive WhatsApp messages (verify signature, ack 200 quickly).
- `POST /ask` — body `{ question: string, k?: number }` → RAG answer (used internally by webhook and by admin for testing).
- `POST /admin/reindex` — trigger `ingest.py` (protect with a shared secret or run offline).
- (Optional) `GET /admin/health` — readiness/liveness.

All handlers must be **stateless**; do not persist requests or responses.

## 5) RAG Flow (Stateless)
1. Normalize question (trim, language detect optional).
2. **Embed** question (Ollama embeddings).
3. FAISS **search** top-k (e.g., 12) → **rerank** (optional cosine sort) → top-m (e.g., 6).
4. Build prompt:
   - **System**: strict grounding + refusal rule.
   - **Context**: chunk texts + `(filename, page)` for light citations.
   - **User**: the question.
5. **Generate** with local LLM (short, direct).
6. Return `{ answer, sources }`.

## 6) Prompts
**System prompt**
```
You are a concise assistant that answers ONLY using the provided context.
If the answer is not in the context, respond exactly:
"I don't know based on the current knowledge base."
Never fabricate or infer beyond the context. Keep answers short and actionable.
When possible, include brief source notes like (filename).
```

**User prompt template**
```
Context:
{{top_chunks_joined_with_separators}}

User question: {{question}}

Answer:
```

## 7) WhatsApp Wiring (Cloud API)
- Set webhook URL and **verify X-Hub-Signature-256**.
- On inbound text:
  1) `res.sendStatus(200)` immediately.
  2) Call `/ask` with the text; get `{answer}`.
  3) Send **text message** back via WhatsApp Messages API.
- **DO NOT** send templates or proactive pings after 24h of silence.
- Add light rate-limiting in memory (per number per minute) to avoid loops.

## 8) No-Storage Guarantee
- Turn off request body logging or **redact** message content in logs.
- Keep only counters like `answers_count_total` in memory; zero PII.
- For debugging, use a **sandbox mode** that prints to console but never persists.

## 9) Admin KB Workflow
- Put files into `admin/kb/`.
- Run:
  ```bash
  python admin/ingest.py
  ```
- Hot-reload: keep FAISS in memory; add a file watcher (optional) to reload index on change.

## 10) Quality & UX to Keep the Window “Free”
- Every reply ends with a soft nudge:  
  “Want a shorter summary or the original doc link?”  
- If an answer is long, send it as 1–2 messages **within the same window** (free).
- Never schedule reminders; let users send “update” to fetch again.

## 11) Security & Safety
- Verify webhook signature.
- Shared secret on `/admin/reindex`.
- Blocklist categories you don’t want to answer (regex) → return safe refusal.
- Timeouts: embeddings (2s), retrieval (100ms), generation (≤8s); return graceful fallback.

## 12) Testing & Acceptance
**Unit**
- Retrieval returns expected chunks for seed questions.
- Empty context → exact fallback string.

**Integration**
- Golden set (20–50 Q/As) with expected source filenames—run on every reindex.

**Manual**
- Upload 3–5 sample PDFs; ask 10 varied questions; confirm:
  - answers grounded with correct source hints,
  - out-of-scope returns the exact fallback,
  - no logs contain message text.

## 13) Performance Goals
- Retrieval: < 150ms
- LLM generation: 1.5–3.0s for ~120 tokens
- End-to-end p50: < 3.5s

## 14) “Day 1” Build Checklist
- [ ] Create Meta WA Cloud API app + webhook.
- [ ] `admin/ingest.py` working on 2–3 files.
- [ ] `POST /ask` returns grounded answers with source hints.
- [ ] Webhook receives WA text and replies via Messages API.
- [ ] Logging shows no PII; only status + durations.

## 15) Nice-to-Have (Later)
- Language auto-detect & translate.
- Inline citations.
- Simple admin web UI.
- Eval harness for groundedness and refusal rate.
