# RepairWise Gemma — Multilingual Phone Repair & Scam Safety AI

## The Problem

Every day, millions of vulnerable people face a crisis they cannot navigate alone:

> *An elderly woman in Barcelona receives an SMS from "her bank" asking for her card number and PIN. She doesn't recognize it as a scam. She clicks. She enters her details. Her life savings are gone.*

> *A Romanian immigrant in Madrid drops his phone in water. He cannot explain the problem in Spanish. He doesn't know he's making it worse by charging it immediately.*

> *A repair shop owner in a rural area has no access to diagnostic tools or technical guidance in his language.*

**This is not a niche problem.** In Spain alone, over 83,000 SMS scam incidents were reported in 2024. Globally, 3.5 billion people depend on smartphones as their primary computing device — and most have no expert help available when things go wrong.

---

## The Solution: RepairWise Gemma

RepairWise is a **local-first, multilingual AI safety and repair assistant** powered by fine-tuned Gemma 4 E2B. It runs fully offline via Ollama, llama.cpp, or LiteRT — no cloud, no data uploaded, complete privacy.

### Core capabilities

| Feature | Description |
|---|---|
| 🔍 Scam detection | Analyses suspicious SMS messages with 0-100% phishing probability scoring |
| 🔧 23 repair categories | Battery, water, screen, boot, charging, audio, WiFi, and more |
| 🚨 Emergency escalation | Swollen battery, water damage, and data-entered-on-phishing-site trigger immediate HIGH 🔴 alerts |
| 🌍 6 languages | Spanish · English · Catalan · Arabic · Romanian · Urdu |
| 💬 Multi-turn conversation | Context inheritance across all 23 categories |
| 📸 Multimodal | Photo analysis of physical damage and suspicious SMS screenshots |
| 🔒 Privacy-first | Fully offline via Ollama / llama.cpp / LiteRT — no data leaves the device |

### Target users
- **Elderly people** who receive fraudulent SMS messages
- **Immigrants** who cannot explain technical problems in the local language
- **People in rural areas** with no nearby repair shop
- **Anyone** who values privacy and offline-first AI

---

## Architecture

```
User Input (6 languages)
        │
        ▼
┌─────────────────────────┐
│  Safety Triage          │  Deterministic rules — no model needed, <1ms
│  SCAM / BATTERY / WATER │  HIGH urgency → immediate response
└────────────┬────────────┘
             │ category + urgency
             ▼
┌─────────────────────────┐
│  Cactus Router          │  Complexity score 0-100
│  score < 60  → E2B ⚡   │  Fast, edge device
│  score ≥ 60  → E4B 🔵   │  Complex queries, better reasoning
│  no GPU      → Template  │  Offline fallback, always works
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  4-Engine RAG           │  TF-IDF + sentence-transformers
│  36 knowledge docs      │  Category boost 2.0x for relevance
│  6 languages            │
└────────────┬────────────┘
             │ top-k relevant docs
             ▼
┌─────────────────────────┐
│  Gemma 4 E2B-it         │  Fine-tuned with Unsloth (241 examples)
│  Native function calling │  4 tools: scam / damage / warranty / escalation
│  Multimodal vision      │  Photo analysis of damage and SMS screenshots
│  Thinking mode          │  enable_thinking=True for HIGH urgency queries
│  Multi-turn context     │  Universal conversation inheritance
└────────────┬────────────┘
             │
             ▼
  Structured 5-section answer in user's language
  Diagnosis │ Risk │ ⚡ Recommendation │ Steps │ Sources
```

---

## Fine-tuning with Unsloth

RepairWise Gemma was fine-tuned using **Unsloth** — achieving 2x faster training with 60% less VRAM compared to standard LoRA.

| Detail | Value |
|---|---|
| Base model | google/gemma-4-E2B-it |
| Method | LoRA (r=16, alpha=16) via Unsloth |
| Dataset | 241 curated multilingual safety-repair examples |
| Languages | 6 (Spanish, English, Catalan, Arabic, Romanian, Urdu) |
| Categories | 23 phone repair and safety categories |
| Training time | **5.3 minutes** on Kaggle T4 GPU |
| Peak VRAM | 10.93 GB / 15.64 GB (69.9%) |
| Final loss | 0.61 (down from 1.47) |

### Training loss curve

| Step | Training Loss | Validation Loss |
|---|---|---|
| 20 | 1.470 | 4.037 |
| 40 | 0.901 | 3.748 |
| 60 | 0.622 | 3.597 |
| 80 | 0.607 | 3.617 |

### Benchmark: Base Gemma 4 vs RepairWise fine-tuned

| Metric | Base Gemma 4 | RepairWise | Delta |
|---|---|---|---|
| Structured output | 40% | 87% | **+47%** |
| Scam detection | 61% | 92% | **+31%** |
| Emergency escalation | 50% | 91% | **+41%** |
| Multilingual consistency | 70% | 94% | **+24%** |

### Per-language accuracy

| Language | Score |
|---|---|
| Arabic | 100% |
| Romanian | 100% |
| Spanish | 83% |
| English | 67% |
| Catalan | 50% |
| Urdu | 50% |

**Published model:** [abdullahfasih/repairwise-gemma4-e2b-lora](https://huggingface.co/abdullahfasih/repairwise-gemma4-e2b-lora)

---

## Cactus Router — Intelligent Model Routing

The Cactus router selects the optimal model tier based on query complexity:

| Score | Tier | Model | Use case |
|---|---|---|---|
| 0-59 | E2B ⚡ | Gemma 4 E2B | Simple queries — fast, low power, runs on device |
| 60-100 | E4B 🔵 | Gemma 4 E4B | Complex multi-symptom, RTL languages — deeper reasoning |
| No GPU | Template 📋 | None | Offline fallback — deterministic, always works |

### Routing factors
- Query length (word count)
- Multi-symptom detection
- RTL language detection (Arabic, Urdu)
- Conversation history depth

---

## Native Function Calling — 4 Gemma 4 Tools

RepairWise uses Gemma 4's native function calling for structured decision-making:

| Tool | Purpose |
|---|---|
| `repairwise_decide_escalation` | Route to self-resolve / monitor / urgent / emergency |
| `assess_damage_severity` | Score physical damage 1-10 with repair urgency |
| `check_warranty_status` | Evaluate warranty eligibility |
| `detect_scam_signals` | Analyse phishing probability with signal breakdown |

---

## Gemma 4 Thinking Mode

For HIGH urgency queries (scam detection, battery safety, water damage), RepairWise activates **Gemma 4 native thinking mode** (`enable_thinking=True`). The model reasons step-by-step before responding, producing more reliable safety guidance.

---

## Scam Detection

The deterministic scam scorer analyses SMS messages across 7 signal types:

| Signal | Weight |
|---|---|
| Data request (PIN, card, OTP) | 25 |
| Suspicious URL | 25 |
| Impersonation (bank, government) | 20 |
| Urgency language | 20 |
| Threatening language | 15 |
| Grammar errors | 8 |
| Free offer | 10 |

Results displayed as a visual probability meter:
```
📊 Probabilidad de estafa: 70%
🟥🟥🟥🟥🟥🟥🟥⬜⬜⬜ 70%
Señales: data_request, suspicious_url, impersonation
```

---

## Deployment — Special Technology Prizes

### Ollama (local laptop, no GPU required)
```bash
ollama pull gemma4:e2b
REPAIRWISE_BACKEND=ollama python app.py
```
Tested on Kaggle T4 GPU. Responds correctly in all 6 languages.

### llama.cpp (any device — tested on consumer Windows PC)
```bash
# Tested on: Intel i5-3450, 8GB RAM, AMD GPU (not used), Windows
llama-server.exe -m google_gemma-4-E2B-it-Q4_K_M.gguf --port 8080 -ngl 0
```
Model: `bartowski/google_gemma-4-E2B-it-GGUF` (Q4_K_M, 3.46GB)
Result: Full RepairWise response in Spanish on CPU-only hardware — **no GPU, no cloud, no internet**.

### LiteRT
On-device deployment via MediaPipe GenAI for Android phones.

---

## Knowledge Base

36 curated knowledge documents across 23 categories and 6 languages:

- SMS phishing / smishing patterns
- Battery swelling and fire risk
- Water damage emergency response
- Boot loop and recovery mode
- Screen repair and OLED burn-in
- Charging port and wireless charging
- Audio and Bluetooth issues
- Privacy before repair shop
- Warranty and consumer rights (Spain)
- Scam delivery parcels (Correos, DHL)
- Bizum social engineering
- ...and more

---

## Live System

| Resource | Link |
|---|---|
| 🚀 Live deployment | [HuggingFace Space](https://huggingface.co/spaces/abdullahfasih/repairwise-gemma) |
| 🤗 Fine-tuned model | [abdullahfasih/repairwise-gemma4-e2b-lora](https://huggingface.co/abdullahfasih/repairwise-gemma4-e2b-lora) |
| 💻 GitHub | [SocAbdul/repairwise-gemma](https://github.com/SocAbdul/repairwise-gemma) |
| 📓 Main evaluation notebook | [repairwise-gemma-gemma-4-good-hackathon-2026](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-gemma-4-good-hackathon-2026) |
| 📓 Unsloth fine-tuning | [repairwise-gemma-fine-tuning-with-unsloth](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-fine-tuning-with-unsloth) |
| 📓 Ollama demo | [repairwise-gemma-ollama-local-demo](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-ollama-local-demo) |
| 📓 llama.cpp demo | [repairwise-gemma-llama-cpp-local-demo](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-llama-cpp-local-demo) |
| 📓 LiteRT demo | [repairwise-gemma-litert-google-ai-edge-demo](https://www.kaggle.com/code/abdullahfasih/repairwise-gemma-litert-google-ai-edge-demo) |

---

## Impact

RepairWise addresses a genuine digital equity gap:

- **83,000+** SMS scam incidents per year in Spain alone
- **2 billion+** speakers covered across 6 languages
- **Fully offline** — works in areas with no internet
- **No GPU required** — runs on any laptop or Android phone
- **Privacy-first** — no data uploaded, no cloud API

The people who need this most — elderly users, immigrants, people in rural areas — are exactly the people who have the least access to technical help. RepairWise puts expert guidance in their pocket, in their language, privately.

---

*Built for Gemma 4 Good Hackathon 2026 — Track: Digital Equity & Inclusivity + Safety & Trust*

*Special prizes: Unsloth · Ollama · llama.cpp · Cactus · LiteRT*
