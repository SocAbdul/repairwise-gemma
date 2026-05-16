# 📱 RepairWise Gemma
### Offline Multilingual Phone Repair & Scam Safety AI

> *For the next billion smartphone users who need expert help — in their own language, privately, without internet.*

[![HuggingFace Space](https://img.shields.io/badge/🚀_Live_Demo-HuggingFace_Space-blue)](https://huggingface.co/spaces/abdullahfasih/repairwise-gemma)
[![Model](https://img.shields.io/badge/🤗_Model-repairwise--gemma4--e2b--lora-yellow)](https://huggingface.co/abdullahfasih/repairwise-gemma4-e2b-lora)
[![Kaggle](https://img.shields.io/badge/📓_Notebook-Kaggle-orange)](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-gemma-4-good-hackathon-2026)
[![License](https://img.shields.io/badge/License-Apache_2.0-green)](LICENSE)

Built for the **Gemma 4 Good Hackathon 2026** — Track: Digital Equity & Inclusivity + Safety & Trust

---

## The Problem

Every day, millions of vulnerable people face crises they cannot navigate alone:

- 👴 An **elderly woman** receives a phishing SMS from "her bank" — she loses her savings
- 🌍 An **immigrant** cannot explain a technical problem in the local language
- 🏘️ A person in a **rural area** has no nearby repair shop
- 🔐 Everyone deserves **privacy** — no cloud, no data uploaded

**83,000+ SMS scam incidents per year in Spain alone.**

---

## Solution

RepairWise Gemma is a **local-first multilingual AI** powered by fine-tuned Gemma 4 E2B that:

- 🔍 **Detects SMS scams** with 0-100% phishing probability scoring
- 🔧 **Diagnoses 23 phone repair categories** with structured guidance
- 🚨 **Escalates emergencies** (swollen battery, water damage) immediately
- 🌍 **Responds in 6 languages** — Spanish · English · Catalan · Arabic · Romanian · Urdu
- 💬 **Holds conversations** — multi-turn context across all categories
- 📸 **Analyses photos** of physical damage or suspicious SMS screenshots
- 🔒 **Runs fully offline** via Ollama / llama.cpp / LiteRT

---

## Quick Start

### Option 1 — HuggingFace Space (live, no install)
```
https://huggingface.co/spaces/abdullahfasih/repairwise-gemma
```

### Option 2 — Ollama (local laptop)
```bash
ollama pull gemma4:e2b
git clone https://github.com/SocAbdul/repairwise-gemma
cd repairwise-gemma
pip install -r requirements.txt
REPAIRWISE_BACKEND=ollama python app.py
```

### Option 3 — llama.cpp (any device, no GPU)
```bash
# Download: https://github.com/ggerganov/llama.cpp/releases
llama-server.exe -m google_gemma-4-E2B-it-Q4_K_M.gguf --port 8080 -ngl 0
REPAIRWISE_BACKEND=llamacpp python app.py
```

### Option 4 — Transformers (GPU)
```bash
git clone https://github.com/SocAbdul/repairwise-gemma
cd repairwise-gemma
pip install -r requirements.txt
python app.py
```

---

## Architecture

```
User Input (6 languages)
        │
        ▼
[Safety Triage]          → Deterministic, <1ms, no model needed
   SCAM / BATTERY / WATER → HIGH urgency → immediate response
        │
        ▼
[Cactus Router]          → Complexity score 0-100
   score < 60  → E2B ⚡  → Fast, edge device
   score ≥ 60  → E4B 🔵  → Complex queries, better reasoning
   no GPU      → Template → Offline fallback
        │
        ▼
[4-Engine RAG]           → TF-IDF + sentence-transformers
   36 knowledge docs     → Category boost 2.0x
   6 languages           →
        │
        ▼
[Gemma 4 E2B-it]         → Fine-tuned with Unsloth
   4 native tools        → scam / damage / warranty / escalation
   Thinking mode         → enable_thinking=True for HIGH urgency
   Multimodal vision     → photo analysis
   Multi-turn context    → universal conversation inheritance
        │
        ▼
  Structured 5-section answer in user's language
```

---

## Fine-tuning (Unsloth)

| Detail | Value |
|---|---|
| Base model | google/gemma-4-E2B-it |
| Method | LoRA (r=16) via Unsloth |
| Dataset | 241 curated multilingual examples |
| Training time | **5.3 minutes** on T4 GPU |
| Final loss | 0.61 (from 1.47) |

**Benchmark improvement:**
| Metric | Base | Fine-tuned |
|---|---|---|
| Structured output | 40% | 87% |
| Scam detection | 61% | 92% |
| Emergency escalation | 50% | 91% |

---

## Notebooks

| Notebook | Description | Prize |
|---|---|---|
| [Main Evaluation](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-gemma-4-good-hackathon-2026) | Gemma 4 real inference, thinking mode, function calling, benchmark | Main track |
| [Unsloth Fine-tuning](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-fine-tuning-with-unsloth) | Full training pipeline, loss curves, before/after benchmark | Unsloth $10k |
| [Ollama Demo](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-ollama-local-demo) | Local inference via Ollama, 6 languages, multimodal | Ollama $10k |
| [llama.cpp Demo](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-llama-cpp-local-demo) | CPU-only inference on consumer Windows PC | llama.cpp $10k |
| [LiteRT Demo](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-litert-google-ai-edge-demo) | Android deployment, MediaPipe GenAI, 5-backend comparison | LiteRT $10k |

---

## Special Technology Prizes

| Prize | Implementation |
|---|---|
| 🏆 Unsloth $10k | Fine-tuned Gemma 4 E2B with Unsloth LoRA, published to HuggingFace |
| 🏆 Ollama $10k | Full Ollama backend, streaming, 6 languages, multimodal |
| 🏆 llama.cpp $10k | GGUF inference tested on Intel i5 CPU, no GPU, Windows |
| 🏆 LiteRT $10k | MediaPipe GenAI path, Android architecture, Kotlin integration |
| 🏆 Cactus $10k | Complexity-based E2B/E4B routing with 0-100 scoring |

---

## Repository Structure

```
repairwise-gemma/
├── engine.py              # Core engine (3300+ lines)
│   ├── Safety triage      # Deterministic, no model needed
│   ├── Cactus router      # E2B/E4B/template routing
│   ├── 4-engine RAG       # TF-IDF + semantic retrieval
│   ├── Scam scorer        # 0-100% phishing probability
│   └── Multi-turn context # Universal conversation inheritance
├── app.py                 # Gradio UI with visual identity
├── data_pack.py           # Knowledge base (36 docs, 6 languages)
├── run_ollama.py          # Standalone Ollama CLI
├── requirements.txt
└── notebooks/
    ├── repairwise_evaluation.ipynb
    ├── repairwise_finetune_unsloth.ipynb
    ├── repairwise_ollama_demo.ipynb
    ├── repairwise_llamacpp_demo.ipynb
    └── repairwise_litert_demo.ipynb
```

---

## Links

| Resource | URL |
|---|---|
| 🚀 Live deployment | https://huggingface.co/spaces/abdullahfasih/repairwise-gemma |
| 🤗 Fine-tuned model | https://huggingface.co/abdullahfasih/repairwise-gemma4-e2b-lora |
| 💻 GitHub | https://github.com/SocAbdul/repairwise-gemma |

---

## License

Apache 2.0 — same as Gemma 4.

---

*Built for Gemma 4 Good Hackathon 2026*
*Digital Equity & Inclusivity + Safety & Trust + 5 Special Technology Prizes*
