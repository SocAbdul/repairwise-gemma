# 📱 RepairWise Gemma

> **Local-first multilingual phone repair and scam safety assistant — powered by fine-tuned Gemma 4 E2B**

[![Gemma 4 Good Hackathon](https://img.shields.io/badge/Gemma%204%20Good-Hackathon%202026-blue?style=flat-square)](https://www.kaggle.com/competitions/gemma-4-good-hackathon)
[![HF Model](https://img.shields.io/badge/🤗%20Fine--tuned%20Model-abdullahfasih/repairwise--gemma4--e2b--lora-orange?style=flat-square)](https://huggingface.co/abdullahfasih/repairwise-gemma4-e2b-lora)
[![HF Space](https://img.shields.io/badge/🤗%20Live%20Demo-Hugging%20Face%20Spaces-yellow?style=flat-square)](https://huggingface.co/spaces/abdullahfasih/repairwise-gemma)
[![License](https://img.shields.io/badge/license-Apache%202.0-green?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square)](https://python.org)

---

## The Problem

Every day, millions of people walk into a phone repair shop with two problems: a broken or compromised phone, and nobody they trust to explain what's wrong — **in a language they understand**.

In Spain alone, INCIBE registered **83,000+ SMS scam incidents in 2023**. The primary victims are elderly users and immigrants — the same populations least equipped to recognise a fake bank message or understand what a swollen battery means.

**RepairWise Gemma closes that gap — locally, privately, in 6 languages.**

---

## 🎬 Demo

🔗 **[Try it live on Hugging Face Spaces](https://huggingface.co/spaces/abdullahfasih/repairwise-gemma)** — no login, no install required

📓 **[RepairWise App Notebook](https://kaggle.com)** — Kaggle (Gemma 4 E2B, GPU)

📓 **[Fine-tuning Notebook](https://kaggle.com)** — Unsloth LoRA training + benchmark

🤗 **[Fine-tuned Weights](https://huggingface.co/abdullahfasih/repairwise-gemma4-e2b-lora)** — `abdullahfasih/repairwise-gemma4-e2b-lora`

---

## What it does

| Feature | Detail |
|---|---|
| 🔴 SMS phishing detection | Analyses text + optional screenshot with Gemma 4 vision |
| 🔋 Battery swelling / fire risk | HIGH urgency triage — immediate safety steps |
| 💧 Water damage | Emergency response — stop charging, no heat |
| 📱 23 problem categories | Screen, charging, boot, wifi, camera, storage, bluetooth... |
| 🌍 6 languages | Spanish · English · Catalan · Arabic · Romanian · Urdu |
| 🔒 Privacy-first | No cloud API, no data stored, runs fully locally |
| 🤖 Gemma 4 E2B | Fine-tuned · Function calling · Streaming · Multimodal |

---

## Architecture

```
User input (text + optional image)
         │
         ▼
┌─────────────────────────────────┐
│  1. Safety Triage (deterministic)│  Battery fire / phishing → always HIGH
│     23 categories · 3 urgencies │  Never model-dependent for safety
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  2. 4-Engine Hybrid RAG         │  TF-IDF word (0.30)
│     36 knowledge documents      │  TF-IDF char n-gram (0.22)
│     6-language knowledge base   │  Keyword aliases (0.18)
│                                 │  sentence-transformers cosine (0.30)
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│  3. RepairWise Fine-tuned       │  abdullahfasih/repairwise-gemma4-e2b-lora
│     Gemma 4 E2B — 4 routes:    │
│                                 │
│  A) Native function calling     │  escalate_to_technician() tool
│  B) Text enrichment (MED/LOW)   │  Personalised answer from template
│  C) High-risk context (HIGH)    │  One grounded sentence added
│  D) Multimodal photo analysis   │  describe → triage → answer
│                                 │
│  Real TextIteratorStreamer      │  Token-by-token streaming
│  Multi-turn conversation        │  Context from last 3 turns
└────────────────┬────────────────┘
                 │
                 ▼
     Structured 5-section answer
   Diagnosis · Risk · Steps · Referral · Sources
```

---

## Fine-tuning with Unsloth

We fine-tuned Gemma 4 E2B using **Unsloth** on 241 curated multilingual phone repair and scam safety conversations across 6 languages and 17 categories.

```python
from unsloth import FastModel
from unsloth.chat_templates import get_chat_template

model, tokenizer = FastModel.from_pretrained(
    "abdullahfasih/repairwise-gemma4-e2b-lora",
    max_seq_length=2048,
    load_in_4bit=True,
)
tokenizer = get_chat_template(tokenizer, chat_template="gemma-4-thinking")
```

**Training details:**

| Parameter | Value |
|---|---|
| Base model | `google/gemma-4-e2b` (2B params) |
| Method | LoRA r=16, alpha=16 via Unsloth |
| Dataset | 241 examples · 6 languages · 17 categories |
| Epochs | 3 · Batch size 8 · Cosine LR |
| Hardware | Kaggle T4 GPU · 5.5 minutes |
| Final train loss | 0.60 |

**Benchmark (fine-tuned model, 20 test cases):**

| Language | Cases | Accuracy |
|---|---|---|
| Spanish | 6 | 100% |
| English | 6 | 83% |
| Arabic | 2 | 100% |
| Catalan | 2 | 100% |
| Romanian | 2 | 100% |
| Urdu | 2 | 50% |
| **Overall** | **20** | **90%** |

---

## Repository structure

```
repairwise-gemma/
├── app.py              # HF Spaces entry point — model loading + Gradio UI
├── engine.py           # Core pipeline: triage, RAG, Gemma 4 generation
├── data_pack.py        # Knowledge base (36 docs) + 138 multilingual templates
├── requirements.txt    # Python dependencies
├── notebook/
│   ├── repairwise_v17.ipynb              # App notebook (Kaggle)
│   └── repairwise_finetune_unsloth.ipynb # Fine-tuning notebook (Kaggle)
└── README.md
```

---

## Running locally

```bash
git clone https://github.com/SocAbdul/repairwise-gemma
cd repairwise-gemma
pip install -r requirements.txt

# With GPU (recommended):
HF_TOKEN=your_hf_token python app.py

# Demo mode (no GPU — template responses):
python app.py
```

Open `http://localhost:7860` in your browser.

---

## Gemma 4 features used

| Feature | Implementation |
|---|---|
| ✅ Multimodal input | Image + text → Gemma 4 vision encoder |
| ✅ Native function calling | `escalate_to_technician()` with JSON schema |
| ✅ Real token streaming | `TextIteratorStreamer` + `threading.Thread` |
| ✅ Multi-turn conversation | Last 3 turns injected as context |
| ✅ Multilingual generation | 6 languages from single fine-tuned model |
| ✅ Edge-optimised | E2B (2B params) · runs on T4 · deployable offline |
| ✅ Fine-tuning (Unsloth) | LoRA domain adaptation · published weights |

---

## Target users

- 👴 **Elderly users** who cannot recognise phishing SMS
- 🌍 **Immigrants** needing support in Arabic, Romanian, Urdu, Catalan
- 🔧 **Small phone repair shops** serving multilingual communities
- 📱 **Anyone** without a trusted tech advisor nearby

---

## Tracks & Prizes

- 🏆 **Main Track** — Digital Equity & Inclusivity
- 🛡️ **Impact Track** — Safety & Trust
- ⚡ **Special Technology Prize** — Unsloth ($10,000)

---

## License

Apache 2.0 — see [LICENSE](LICENSE)

---

## 🦙 Running with Ollama (no GPU needed)

RepairWise supports **Ollama as a backend** — run Gemma 4 E2B locally on any machine without a GPU, without a HuggingFace token, without CUDA.

```bash
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh   # Linux/Mac
# Windows: https://ollama.ai/download

# 2. Pull Gemma 4 E2B
ollama pull gemma4:e2b

# 3. Clone RepairWise
git clone https://github.com/SocAbdul/repairwise-gemma
cd repairwise-gemma
pip install -r requirements.txt

# 4. Run with Ollama backend
REPAIRWISE_BACKEND=ollama python app.py

# Or use the standalone CLI (no Gradio needed):
python run_ollama.py
```

### Ollama backend architecture

```
User query
    │
    ▼
RepairWise Engine (Python)
  Safety Triage ─── deterministic, always runs
  4-Engine RAG ──── local embeddings, no internet
  Ollama Client ─── HTTP POST to localhost:11434
    │
    ▼
Ollama Server (localhost)
  gemma4:e2b ─── quantized, runs on CPU (8GB RAM)
                  or GPU if available
```

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `REPAIRWISE_BACKEND` | `transformers` | `ollama` or `transformers` or `auto` |
| `OLLAMA_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `gemma4:e2b` | Model to use |

`auto` mode: tries Ollama first, falls back to transformers if not available.


---

*Built for the [Gemma 4 Good Hackathon 2026](https://www.kaggle.com/competitions/gemma-4-good-hackathon)*
*Fine-tuned weights: [abdullahfasih/repairwise-gemma4-e2b-lora](https://huggingface.co/abdullahfasih/repairwise-gemma4-e2b-lora)*
