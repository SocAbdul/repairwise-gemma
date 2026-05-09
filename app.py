"""
RepairWise Gemma — Hugging Face Spaces entry point
===================================================
Local-first multilingual phone repair + scam safety assistant.
Powered by Gemma 4 E2B (multimodal, edge-optimised).

Architecture:
  Safety Triage → 4-Engine Hybrid RAG → Gemma 4 (function calling + streaming)

Tracks: Digital Equity & Inclusivity · Safety & Trust
Hackathon: Gemma 4 Good (Kaggle, 2026)
"""

import os
import sys
import torch
import gradio as gr
import pandas as pd
import json
import threading
from PIL import Image as PILImage, ImageDraw
from transformers import AutoProcessor, AutoModelForImageTextToText, TextIteratorStreamer

# ── Load data pack and engine ─────────────────────────────────────────────────
from data_pack import (
    LOCAL_KNOWLEDGE,
    CATEGORY_RESPONSE_TEMPLATES,
    PHOTO_VISUAL_CATEGORIES,
    SECTION_LABELS,
)
from engine import (
    rebuild_repairwise_indexes,
    try_init_semantic_retriever,
    repairwise_answer,
    repairwise_debug,
    REPAIRWISE_VERSION,
)

# ── Model configuration ───────────────────────────────────────────────────────
# HF Spaces: model loaded from Hugging Face hub.
# Kaggle: override MODEL_PATH to the local dataset path.
MODEL_ID = os.environ.get("MODEL_ID", "abdullahfasih/repairwise-gemma4-e2b-lora")
HF_TOKEN = os.environ.get("HF_TOKEN", None)  # Set in HF Space secrets

DEMO_MODE = False  # Set to True if no GPU available

processor = None
model = None


def load_model():
    """Load RepairWise fine-tuned model (LoRA) or base Gemma 4 E2B.
    Sets DEMO_MODE if no GPU or load fails."""
    global processor, model, DEMO_MODE

    if not torch.cuda.is_available():
        print("⚠️  No GPU detected — running in DEMO MODE (template-only responses)")
        DEMO_MODE = True
        return

    print(f"Loading {MODEL_ID} on GPU: {torch.cuda.get_device_name(0)}")
    IS_LORA = any(x in MODEL_ID.lower() for x in ["lora", "repairwise", "finetune", "ft-"])
    BASE_MODEL = "google/gemma-4-e2b"

    try:
        # Processor always from base model (LoRA adapters don't change processor)
        proc_id = BASE_MODEL if IS_LORA else MODEL_ID
        processor = AutoProcessor.from_pretrained(proc_id, token=HF_TOKEN)

        if IS_LORA:
            # Load base + merge LoRA adapter
            try:
                from peft import PeftModel
                print(f"  Loading base: {BASE_MODEL}")
                base = AutoModelForImageTextToText.from_pretrained(
                    BASE_MODEL,
                    torch_dtype=torch.float16,
                    device_map={"": 0},
                    token=HF_TOKEN,
                )
                print(f"  Merging LoRA adapter: {MODEL_ID}")
                model = PeftModel.from_pretrained(base, MODEL_ID, token=HF_TOKEN)
                model = model.merge_and_unload()
                print(f"✅ RepairWise fine-tuned model loaded and merged")
            except ImportError:
                print("  peft not installed — loading base model instead")
                model = AutoModelForImageTextToText.from_pretrained(
                    BASE_MODEL,
                    torch_dtype=torch.float16,
                    device_map={"": 0},
                    token=HF_TOKEN,
                )
        else:
            model = AutoModelForImageTextToText.from_pretrained(
                MODEL_ID,
                torch_dtype=torch.float16,
                device_map={"": 0},
                token=HF_TOKEN,
            )

        model.eval()
        print(f"✅ Model ready on {model.device}")
    except Exception as e:
        print(f"⚠️  Model load failed: {e}\nRunning in DEMO MODE.")
        DEMO_MODE = True


# ── Initialise indexes and model ─────────────────────────────────────────────
print(f"RepairWise {REPAIRWISE_VERSION} starting...")
rebuild_repairwise_indexes()
try_init_semantic_retriever()
load_model()

# Inject model references into engine module so it can call Gemma
import engine as _engine
_engine.processor = processor
_engine.model = model
_engine.DEMO_MODE = DEMO_MODE

print(f"✅ RepairWise ready | Demo mode: {DEMO_MODE}")


# ── Example assets ────────────────────────────────────────────────────────────
def ensure_demo_assets():
    os.makedirs("./examples", exist_ok=True)

    sms_path = "./examples/sms_phishing_example.png"
    if not os.path.exists(sms_path):
        img = PILImage.new("RGB", (800, 450), "white")
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 800, 60], fill="#CC0000")
        d.text((20, 15), "⚠️  BANK SECURITY ALERT", fill="white")
        d.text((20, 90), "Your account has been SUSPENDED.", fill="black")
        d.text((20, 130), "Verify your identity NOW to restore access:", fill="black")
        d.text((20, 175), "http://secure-bank-verify.example/login", fill="#CC0000")
        d.text((20, 230), "Enter card number + PIN + OTP code", fill="#880000")
        d.text((20, 310), "⚠️  WARNING: Real banks NEVER ask for this by SMS.", fill="#007700")
        img.save(sms_path)

    dark_path = "./examples/dark_unclear_photo.png"
    if not os.path.exists(dark_path):
        img = PILImage.new("RGB", (150, 150), (10, 10, 10))
        img.save(dark_path)

    screen_path = "./examples/cracked_screen_example.png"
    if not os.path.exists(screen_path):
        img = PILImage.new("RGB", (450, 800), (20, 20, 20))
        d = ImageDraw.Draw(img)
        for x in range(0, 450, 30):
            d.line([(x, 0), (x + 150, 800)], fill=(80, 80, 80), width=1)
        d.text((30, 380), "CRACKED SCREEN", fill="white")
        img.save(screen_path)

    return sms_path, dark_path, screen_path


sms_path, dark_path, screen_path = ensure_demo_assets()


# ── Gradio UI ─────────────────────────────────────────────────────────────────
def gradio_repairwise(user_text: str, language: str, image, conversation_state):
    """Main Gradio handler — streams tokens from Gemma 4 or returns template."""
    if not user_text or len(user_text.strip()) < 2:
        yield "", "", "", "", conversation_state, conversation_state.get("chatbot", [])
        return

    history = conversation_state.get("history", [])
    chatbot = conversation_state.get("chatbot", [])

    # Run RepairWise pipeline
    pil_image = PILImage.fromarray(image).convert("RGB") if image is not None else None
    result = repairwise_debug(
        user_text,
        language=language,
        image=pil_image,
        history=history,
    )

    answer = result.get("answer", "")
    meta = result.get("meta", {})
    triage = result.get("triage", {})
    docs = result.get("docs", [])

    # Update history
    history.append({"role": "user", "content": user_text})
    history.append({"role": "assistant", "content": answer})
    chatbot.append((user_text, ""))

    # Stream the answer token by token for visual effect
    partial = ""
    for char in answer:
        partial += char
        chatbot_copy = chatbot[:-1] + [(user_text, partial)]
        yield (
            "",  # clear input
            _format_judge_panel(meta, triage, docs),
            meta.get("sources_used", ""),
            meta.get("gemma_trace", {}).get("raw", "")[:300],
            {**conversation_state, "history": history, "chatbot": chatbot_copy},
            chatbot_copy,
        )

    conversation_state = {**conversation_state, "history": history, "chatbot": chatbot}
    yield (
        "",
        _format_judge_panel(meta, triage, docs),
        meta.get("sources_used", ""),
        meta.get("gemma_trace", {}).get("raw", "")[:300],
        conversation_state,
        chatbot,
    )


def _format_judge_panel(meta: dict, triage: dict, docs: list) -> str:
    """Format the technical debug panel for judges."""
    gemma_trace = meta.get("gemma_trace", {})
    fc = gemma_trace.get("function_calling", {})
    rag_info = meta.get("rag_scores", {})

    lines = [
        f"🔍 RepairWise {REPAIRWISE_VERSION} | Demo mode: {DEMO_MODE}",
        f"",
        f"TRIAGE",
        f"  Category : {triage.get('category', '?')}",
        f"  Urgency  : {triage.get('urgency', '?')}",
        f"  Reason   : {triage.get('reason', '?')}",
        f"",
        f"GEMMA 4 USAGE",
        f"  Called   : {gemma_trace.get('called', False)}",
        f"  Route    : {gemma_trace.get('path', 'template')}",
        f"  Fallback : {gemma_trace.get('fallback_used', False)}",
        f"",
        f"FUNCTION CALLING",
        f"  Attempted: {fc.get('attempted', False)}",
        f"  Tool     : {fc.get('tool_name', '-')}",
        f"  Result   : {json.dumps(fc.get('tool_result', {}), ensure_ascii=False)[:120]}",
        f"",
        f"RAG (4-engine hybrid)",
        f"  Semantic : {rag_info.get('semantic_available', False)}",
        f"  Top docs : {[d.get('id', '?') for d in docs[:3]]}",
        f"",
        f"LANGUAGE : {meta.get('language', '?')}",
        f"MULTI-TURN: {meta.get('context_turns_used', 0)} prior turns used",
    ]
    return "\n".join(lines)


def clear_conversation():
    return {"history": [], "chatbot": []}, []


# ── Build Gradio interface ─────────────────────────────────────────────────────
DEMO_BANNER = (
    "\n\n> ⚠️ **Running in DEMO MODE** (no GPU). "
    "Answers use the full safety triage + RAG pipeline with template responses. "
    "For live Gemma 4 generation, see the [Kaggle notebook](#)."
    if DEMO_MODE else ""
)

with gr.Blocks(theme=gr.themes.Soft(), title="RepairWise Gemma") as demo:
    conversation_state = gr.State({"history": [], "chatbot": []})

    gr.Markdown(
        f"# 📱 RepairWise Gemma\n"
        f"**Local-first multilingual phone repair & scam safety assistant · Gemma 4 E2B**\n\n"
        f"Describe your phone problem or paste a suspicious message. "
        f"Optionally upload a photo of the damage or a suspicious SMS screenshot. "
        f"No data is sent to any external server.{DEMO_BANNER}"
    )

    with gr.Row():
        with gr.Column(scale=2):
            chatbot = gr.Chatbot(label="Conversation", height=380)
            txt_input = gr.Textbox(
                label="Describe the problem or paste the suspicious message",
                placeholder="e.g. Me ha llegado un SMS del banco con un link...",
                lines=3,
            )
            with gr.Row():
                lang_drop = gr.Dropdown(
                    choices=["Spanish", "English", "Catalan", "Arabic", "Romanian", "Urdu"],
                    value="Spanish",
                    label="Language / Idioma",
                    scale=2,
                )
                clear_btn = gr.Button("🗑 Clear", scale=1)
            img_input = gr.Image(
                label="Optional: photo of damage or suspicious SMS screenshot",
                type="numpy",
            )
            submit_btn = gr.Button("🔍 Analyse / Analizar", variant="primary")

        with gr.Column(scale=3):
            with gr.Tabs():
                with gr.Tab("🔧 Technical panel (judges)"):
                    judge_panel = gr.Textbox(
                        label="Pipeline trace",
                        lines=22,
                        interactive=False,
                    )
                with gr.Tab("📚 Sources used"):
                    sources_out = gr.Textbox(
                        label="Knowledge sources",
                        lines=6,
                        interactive=False,
                    )
                with gr.Tab("🤖 Gemma raw output"):
                    raw_out = gr.Textbox(
                        label="Raw Gemma 4 generation (before post-processing)",
                        lines=10,
                        interactive=False,
                    )

    submit_btn.click(
        fn=gradio_repairwise,
        inputs=[txt_input, lang_drop, img_input, conversation_state],
        outputs=[txt_input, judge_panel, sources_out, raw_out, conversation_state, chatbot],
    )
    txt_input.submit(
        fn=gradio_repairwise,
        inputs=[txt_input, lang_drop, img_input, conversation_state],
        outputs=[txt_input, judge_panel, sources_out, raw_out, conversation_state, chatbot],
    )
    clear_btn.click(
        fn=clear_conversation,
        inputs=[],
        outputs=[conversation_state, chatbot],
    )

    gr.Examples(
        examples=[
            ["Me ha llegado un SMS del banco con un link y me pide la tarjeta.", "Spanish", None],
            ["Mi batería está hinchada y la pantalla se levanta.", "Spanish", None],
            ["I dropped my phone in water and now it is getting hot.", "English", None],
            ["El meu mòbil no s'encén i es queda al logo.", "Catalan", None],
            ["Telefonul meu nu se încarcă deloc.", "Romanian", None],
            ["مجھے بینک کا ایک پیغام آیا ہے جس میں کارڈ کی تفصیلات مانگی گئی ہیں۔", "Urdu", None],
            ["My screen has a big crack and touch is not working.", "English", None],
            ["Mi wifi no funciona y tampoco el bluetooth.", "Spanish", None],
            ["ما هو ضمان الهاتف في إسبانيا؟", "Arabic", None],
        ],
        inputs=[txt_input, lang_drop, img_input],
        outputs=[txt_input, judge_panel, sources_out, raw_out, conversation_state, chatbot],
        fn=gradio_repairwise,
        cache_examples=False,
        label="Click to try — 6 languages · 9 scenarios",
    )

    gr.Markdown(
        "---\n"
        "🔒 **Privacy-first**: Gemma 4 runs locally. No cloud API. No user data stored or transmitted.\n\n"
        f"Built for the **Gemma 4 Good Hackathon** · Tracks: Digital Equity & Inclusivity + Safety & Trust\n\n"
        "📓 [Kaggle Notebook](#) · 💻 [GitHub](#) · 🎬 [Demo Video](#)"
    )

demo.launch()
