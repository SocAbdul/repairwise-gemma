"""
RepairWise Gemma — Hugging Face Spaces entry point
Powered by fine-tuned Gemma 4 E2B (abdullahfasih/repairwise-gemma4-e2b-lora)
Tracks: Digital Equity & Inclusivity · Safety & Trust · Unsloth Special Prize
Gemma 4 Good Hackathon 2026
"""

import os
import sys
import torch
import gradio as gr
import json
from PIL import Image as PILImage, ImageDraw
from transformers import AutoProcessor, AutoModelForImageTextToText

# ── Load data pack and engine ─────────────────────────────────────────────────
from data_pack import LOCAL_KNOWLEDGE, CATEGORY_RESPONSE_TEMPLATES, PHOTO_VISUAL_CATEGORIES, SECTION_LABELS
from engine import rebuild_repairwise_indexes, try_init_semantic_retriever, repairwise_answer, repairwise_debug, repairwise_stream, REPAIRWISE_VERSION

# ── Model configuration ───────────────────────────────────────────────────────
MODEL_ID   = os.environ.get("MODEL_ID", "abdullahfasih/repairwise-gemma4-e2b-lora")
HF_TOKEN   = os.environ.get("HF_TOKEN", None)
DEMO_MODE  = False
processor  = None
model      = None

def load_model():
    global processor, model, DEMO_MODE
    # Allow Ollama/llama.cpp to bypass DEMO_MODE even without CUDA
    OLLAMA_ACTIVE = os.environ.get("REPAIRWISE_BACKEND", "").lower() in ("ollama", "llamacpp")
    if not torch.cuda.is_available() and not OLLAMA_ACTIVE:
        print("⚠️  No GPU — DEMO MODE (template responses)")
        DEMO_MODE = True
        return
    if OLLAMA_ACTIVE:
        print(f"✅ Ollama/llama.cpp backend active — skipping GPU check")
        DEMO_MODE = False
        return
    BASE_MODEL = "google/gemma-4-e2b"
    IS_LORA = any(x in MODEL_ID.lower() for x in ["lora", "repairwise", "finetune"])
    try:
        processor = AutoProcessor.from_pretrained(BASE_MODEL if IS_LORA else MODEL_ID, token=HF_TOKEN)
        if IS_LORA:
            from peft import PeftModel
            base = AutoModelForImageTextToText.from_pretrained(BASE_MODEL, torch_dtype=torch.float16, device_map={"": 0}, token=HF_TOKEN)
            model = PeftModel.from_pretrained(base, MODEL_ID, token=HF_TOKEN)
            model = model.merge_and_unload()
        else:
            model = AutoModelForImageTextToText.from_pretrained(MODEL_ID, torch_dtype=torch.float16, device_map={"": 0}, token=HF_TOKEN)
        model.eval()
        print(f"✅ Model loaded: {MODEL_ID}")
    except Exception as e:
        print(f"⚠️  Load failed: {e} — DEMO MODE")
        DEMO_MODE = True

# ── Startup ───────────────────────────────────────────────────────────────────
print(f"RepairWise {REPAIRWISE_VERSION} starting...")
rebuild_repairwise_indexes()
try_init_semantic_retriever()
load_model()
import engine as _engine
_engine.processor = processor
_engine.model = model
_engine.DEMO_MODE = DEMO_MODE
print(f"✅ Ready | Demo mode: {DEMO_MODE}")

# ── Demo assets ───────────────────────────────────────────────────────────────
def ensure_demo_assets():
    os.makedirs("./examples", exist_ok=True)
    sms_path = "./examples/sms_phishing_example.png"
    if not os.path.exists(sms_path):
        img = PILImage.new("RGB", (600, 300), "white")
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, 600, 50], fill="#CC0000")
        d.text((15, 12), "⚠️  BANK SECURITY ALERT", fill="white")
        d.text((15, 70), "Your account has been SUSPENDED.", fill="black")
        d.text((15, 100), "Verify NOW: http://bank-secure-verify.example/login", fill="#CC0000")
        d.text((15, 130), "Enter card number + PIN + OTP code", fill="#880000")
        img.save(sms_path)
    return sms_path

ensure_demo_assets()

# ── Core handler ─────────────────────────────────────────────────────────────
def format_answer_with_visual(answer: str, meta: dict) -> str:
    """Add visual elements: scam meter, risk banner — in the user's language."""
    triage = meta.get("triage", {})
    scam   = meta.get("scam_analysis") or {}
    cat    = triage.get("category", "")
    urg    = triage.get("urgency", "LOW")
    lang   = meta.get("language", "Spanish")

    prefix = ""

    # Translations for scam meter
    SCAM_METER_LABELS = {
        "Spanish":  ("📊 Probabilidad de estafa", "Señales"),
        "English":  ("📊 Scam Probability",       "Signals"),
        "Catalan":  ("📊 Probabilitat d'estafa",   "Senyals"),
        "Arabic":   ("📊 احتمالية الاحتيال",       "الإشارات"),
        "Romanian": ("📊 Probabilitate înșelătorie","Semnale"),
        "Urdu":     ("📊 فراڈ کا امکان",           "اشارے"),
    }

    RISK_BANNERS = {
        "scam_phishing": {
            "Spanish":  "🚨 **ESTAFA DETECTADA** — No hagas clic ni compartas datos",
            "English":  "🚨 **SCAM DETECTED** — Do not click or share any data",
            "Catalan":  "🚨 **ESTAFA DETECTADA** — No facis clic ni comparteixis dades",
            "Arabic":   "🚨 **تم اكتشاف احتيال** — لا تنقر ولا تشارك أي بيانات",
            "Romanian": "🚨 **ÎNȘELĂTORIE DETECTATĂ** — Nu da click și nu partaja date",
            "Urdu":     "🚨 **فراڈ پکڑا گیا** — لنک پر کلک نہ کریں، ڈیٹا شیئر نہ کریں",
        },
        "scam_clicked_link": {
            "Spanish":  "🚨 **ENLACE ABIERTO** — Actúa ahora mismo",
            "English":  "🚨 **LINK OPENED** — Act immediately",
            "Catalan":  "🚨 **ENLLAÇ OBERT** — Actua ara mateix",
            "Arabic":   "🚨 **تم فتح الرابط** — تصرف فوراً",
            "Romanian": "🚨 **LINK DESCHIS** — Acționează imediat",
            "Urdu":     "🚨 **لنک کھولا گیا** — ابھی کارروائی کریں",
        },
        "scam_data_entered": {
            "Spanish":  "🆘 **EMERGENCIA** — Llama a tu banco AHORA MISMO",
            "English":  "🆘 **EMERGENCY** — Call your bank RIGHT NOW",
            "Catalan":  "🆘 **EMERGÈNCIA** — Truca al teu banc ARA MATEIX",
            "Arabic":   "🆘 **طوارئ** — اتصل بالبنك الآن فوراً",
            "Romanian": "🆘 **URGENȚĂ** — Sună banca ACUM",
            "Urdu":     "🆘 **ایمرجنسی** — ابھی بینک کو کال کریں",
        },
        "battery_safety": {
            "Spanish":  "⚠️ **RIESGO DE INCENDIO** — Deja de usar el móvil AHORA",
            "English":  "⚠️ **FIRE RISK** — Stop using the device immediately",
            "Catalan":  "⚠️ **RISC D'INCENDI** — Deixa d'usar el mòbil ARA",
            "Arabic":   "⚠️ **خطر حريق** — أوقف استخدام الهاتف الآن فوراً",
            "Romanian": "⚠️ **RISC DE INCENDIU** — Oprește utilizarea imediat",
            "Urdu":     "⚠️ **آگ کا خطرہ** — ابھی فون استعمال کرنا بند کریں",
        },
        "water_damage": {
            "Spanish":  "⚠️ **DAÑO POR AGUA** — Apaga el móvil inmediatamente",
            "English":  "⚠️ **WATER DAMAGE** — Power off immediately",
            "Catalan":  "⚠️ **DANY PER AIGUA** — Apaga el mòbil immediatament",
            "Arabic":   "⚠️ **ضرر مائي** — أوقف تشغيل الهاتف فوراً",
            "Romanian": "⚠️ **DAUNE ADE APĂ** — Oprește telefonul imediat",
            "Urdu":     "⚠️ **پانی کا نقصان** — فوری فون بند کریں",
        },
        "overheating_issue": {
            "Spanish":  "⚠️ **SOBRECALENTAMIENTO** — Apaga y deja enfriar",
            "English":  "⚠️ **OVERHEATING** — Power off and let it cool",
            "Catalan":  "⚠️ **SOBREESCALFAMENT** — Apaga i deixa refredar",
            "Arabic":   "⚠️ **ارتفاع حرارة** — أوقف التشغيل واتركه يبرد",
            "Romanian": "⚠️ **SUPRAÎNCĂLZIRE** — Oprește și lasă să se răcească",
            "Urdu":     "⚠️ **زیادہ گرمی** — بند کریں اور ٹھنڈا ہونے دیں",
        },
    }

    # Scam probability meter
    # Show scam meter only if the message itself triggered scam signals
    _user_msg_has_scam = scam and scam.get("scam_probability", 0) >= 30
    if _user_msg_has_scam:
        prob    = scam["scam_probability"]
        filled  = int(prob / 10)
        color   = "🟥" if prob >= 70 else "🟧" if prob >= 40 else "🟨"
        bar     = color * filled + "⬜" * (10 - filled)
        meter_label, signals_label = SCAM_METER_LABELS.get(lang, SCAM_METER_LABELS["English"])
        raw_signals = scam.get("signals_detected", [])[:3]
        SIGNAL_EMOJI = {
            "data_request": "🔴 data_request",
            "suspicious_url": "⚠️ suspicious_url",
            "impersonation": "🔴 impersonation",
            "urgency_lang": "⚠️ urgency",
            "threatening": "🔴 threatening",
            "free_offer": "⚠️ free_offer",
            "grammar_issues": "⚠️ grammar",
        }
        signals = ", ".join(SIGNAL_EMOJI.get(s, s) for s in raw_signals)
        verdict = scam.get("verdict", "")
        prefix += f"\n**{meter_label}: {prob}%**\n{bar} {prob}%\n"
        if signals:
            prefix += f"*{signals_label}: {signals}*\n"
        prefix += "\n---\n"

    # Risk banner in user's language
    # For scam categories: only show danger banner if the message itself is suspicious
    # (scam_score > 20). If score is 0, the user is likely in a safe follow-up.
    _scam_cats_banner = {"scam_phishing", "scam_clicked_link", "scam_data_entered"}
    _show_banner = urg == "HIGH"
    if cat in _scam_cats_banner and scam and scam.get("scam_probability", 0) == 0:
        _show_banner = False  # user's message itself is not a scam — don't alarm them
    if _show_banner:
        cat_banners = RISK_BANNERS.get(cat, {})
        banner = cat_banners.get(lang, cat_banners.get("English", f"🔴 **HIGH RISK**"))
        if not banner:
            banner = f"🔴 **HIGH RISK** — Immediate action required"
        prefix = f"{banner}\n\n" + prefix

    # Add response time badge if available
    rt = meta.get("response_time_s")
    if rt and rt > 0:
        rt_label = f"⚡ {rt:.1f}s" if rt < 10 else f"⏱️ {rt:.0f}s"
        suffix = f"\n\n<sub>{rt_label} · RepairWise Gemma 4</sub>"
    else:
        suffix = ""

    # Emergency bank contacts for scam_data_entered
    if triage.get("category") == "scam_data_entered":
        emergency_contacts = {
            "Spanish":  "\n\n> 📞 **Bancos españoles 24h:** BBVA `900 102 801` · Santander `915 123 123` · CaixaBank `900 40 40 90` · Sabadell `902 323 555`\n> 🚨 **INCIBE:** `017` (gratis, 9h-21h) · Denuncia online: `policia.es`",
            "English":  "\n\n> 📞 **Emergency:** Call your bank's 24h fraud line immediately · UK: Action Fraud `0300 123 2040`",
            "Catalan":  "\n\n> 📞 **Bancs d'urgència 24h:** BBVA `900 102 801` · Santander `915 123 123` · CaixaBank `900 40 40 90`\n> 🚨 **INCIBE:** `017` (gratis) · Denuncia: `mossos.gencat.cat`",
            "Arabic":   "\n\n> 📞 **اتصل بالبنك فوراً** على خط الاحتيال 24 ساعة · **INCIBE:** `017` (مجاني)",
            "Romanian": "\n\n> 📞 **Sună banca ACUM** pe linia de urgențe 24h · **CERT-RO:** `1911`",
            "Urdu":     "\n\n> 📞 **ابھی بینک کو کال کریں** — 24 گھنٹے فراڈ لائن · **FIA:** `9911`",
        }
        ec = emergency_contacts.get(lang, emergency_contacts["English"])
        suffix = ec + suffix

    return prefix + answer + suffix


def _make_status_bubble(text: str) -> str:
    """Format a __STATUS__: message as a clean pipeline progress display."""
    lines = text.replace("__STATUS__:", "").strip().split("\n")
    formatted = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        formatted.append(line)
    body = "\n".join(formatted)
    return f"**🔄 Pipeline en ejecución...**\n```\n{body}\n```"


def repairwise_chat(user_text, language, image, history):
    """True streaming handler with live pipeline status.
    Each pipeline phase (triage, RAG, tools, Gemma) yields an update
    so judges see the AI working in real-time — no frozen screen.
    """
    if not user_text or len(user_text.strip()) < 2:
        yield history, "", "", "", ""
        return

    pil_image = None
    if image is not None:
        try:
            pil_image = PILImage.fromarray(image).convert("RGB")
        except Exception:
            pass

    conv_history = []
    for msg in (history or []):
        if isinstance(msg, dict):
            conv_history.append({"role": msg.get("role", "user"), "content": str(msg.get("content", ""))})
        elif isinstance(msg, (list, tuple)) and len(msg) == 2:
            if msg[0]: conv_history.append({"role": "user", "content": str(msg[0])})
            if msg[1]: conv_history.append({"role": "assistant", "content": str(msg[1])})

    lang = language or "Spanish"

    def _live(content):
        """Build history with current live content in last assistant msg."""
        return list(history or []) + [
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": content},
        ]

    # ── Instant: show user msg + initial spinner ──────────────────────────────
    yield _live("⏳ Iniciando análisis..."), "⏳ Procesando...", "", "", ""

    answer = ""
    meta   = {}
    panel_live = "⏳ Procesando..."

    import time as _t_chat
    _chat_start = _t_chat.time()
    try:
        for chunk, is_final, meta in repairwise_stream(
            user_text, language=lang, image=pil_image, conversation_history=conv_history
        ):
            if is_final:
                answer = chunk
                break

            if chunk.startswith("__STATUS__:"):
                # Pipeline status update — show as formatted progress block
                status_display = _make_status_bubble(chunk)
                panel_live = chunk.replace("__STATUS__:", "").strip()
                yield _live(status_display), panel_live, "", "", ""
            else:
                # Actual tokens arriving — show directly in chatbot
                # First token: clear the status block and start showing answer
                yield _live(chunk), panel_live, "", "", ""

    except Exception as e:
        answer = f"Error: {str(e)[:200]}"
        meta = {}

    # Add response time to meta for format_answer_with_visual
    if meta:
        meta["response_time_s"] = _t_chat.time() - _chat_start

    triage = meta.get("triage", {})

    # ── Phase 3: final answer + visual formatting + debug panel ──────────────
    visual_answer = format_answer_with_visual(answer, meta)
    history = list(history or []) + [
        {"role": "user", "content": user_text},
        {"role": "assistant", "content": visual_answer},
    ]

    gemma        = meta.get("gemma", {})
    fc           = gemma.get("function_calling", {})
    sources_list = meta.get("sources", [])
    router       = meta.get("cactus_router", {})
    scam         = meta.get("scam_analysis") or {}
    is_demo      = DEMO_MODE

    fc_tool   = fc.get("tool_name", "")
    fc_result = str(fc.get("tool_result", {}))[:90]
    if is_demo and not fc_tool:
        fc_status = "Running on HF Free Tier — GPU notebook: see Kaggle"
    elif fc_tool:
        fc_status = f"Tool: {fc_tool} | Result: {fc_result}"
    else:
        fc_status = "Not triggered"

    triage_cat = triage.get("category", "")
    rag_matching = [d.get("id","?") for d in sources_list if d.get("category") == triage_cat][:3]
    rag_ids = rag_matching if rag_matching else [d.get("id","?") for d in sources_list[:3]]

    panel = (
        f"RepairWise {REPAIRWISE_VERSION} | GPU: {'Available' if not is_demo else 'HF Free Tier (no GPU)'}\n\n"
        f"CACTUS ROUTER 🦁\n"
        f"  Tier      : {router.get('selected_tier','?').upper()}\n"
        f"  Complexity: {router.get('complexity_score','?')}/100\n"
        f"  Reason    : {router.get('reason','?')[:65]}\n\n"
        f"TRIAGE\n"
        f"  Category : {triage.get('category','?')}\n"
        f"  Urgency  : {triage.get('urgency','?')}\n"
        f"  Reason   : {triage.get('reason','?')[:60]}\n\n"
        f"GEMMA 4 ({gemma.get('backend','ollama').upper()})\n"
        f"  Called   : {gemma.get('called', False)}\n"
        f"  Route    : {gemma.get('path', 'template')}\n\n"
        f"FUNCTION CALLING (4 tools)\n"
        f"  {fc_status}\n\n"
        + (f"SCAM ANALYSIS 🔍\n"
           f"  Score    : {scam.get('scam_probability','?')}%\n"
           f"  Signals  : {scam.get('signals_detected',[])}\n\n"
           if scam else "") +
        f"RAG  : {rag_ids}\n"
        f"Lang : {meta.get('language','?')}\n"
        f"Hist : {meta.get('history_used', False)}"
    )

    triage_cat_src = triage.get("category", "")
    matching_sources = [d.get("id","?") for d in sources_list if d.get("category") == triage_cat_src]
    sources = " | ".join(matching_sources) if matching_sources else " | ".join([d.get("id","?") for d in sources_list[:3]])
    raw = str(gemma.get("raw_output", gemma.get("raw", "")))[:300]

    yield history, panel, sources, raw, ""

def clear_chat():
    return [], "", "", "", ""  # Gradio 5 messages format

# ── Gradio UI ─────────────────────────────────────────────────────────────────
DEMO_BANNER = (
    "\n\n> ⚠️ **DEMO MODE (HF Free Tier)** — Full triage + RAG + function calling pipeline active. "
    "Responses use safety-validated templates (same pipeline as Gemma 4 generation). "
    "For live Gemma 4 token streaming, run locally with `REPAIRWISE_BACKEND=ollama` or see the [Kaggle notebook](https://kaggle.com)."
    if DEMO_MODE else ""
)

# Pre-baked demo examples for HF Space showcase (shown in placeholder)
DEMO_EXAMPLES = [
    ["Me ha llegado un SMS del banco con un link y me pide la tarjeta y el PIN.", "Spanish"],
    ["My phone battery is swollen and the screen is lifting.", "English"],
    ["مجھے بینک کا مشکوک پیغام آیا جس میں PIN مانگا گیا۔", "Urdu"],
    ["El meu mòbil no s'encén i es queda al logo.", "Catalan"],
    ["بطارية هاتفي منتفخة والشاشة ترتفع عن الجسم.", "Arabic"],
]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { box-sizing: border-box; }
body, .gradio-container { font-family: 'Inter', sans-serif !important; }

/* ── HERO ─────────────────────────────────────────────────────────────── */
.rw-hero {
    background: linear-gradient(135deg, #0a1628 0%, #0d47a1 50%, #1565c0 100%);
    border-radius: 20px;
    padding: 48px 40px 36px;
    margin-bottom: 0;
    color: white;
    position: relative;
    overflow: hidden;
}
.rw-hero::before {
    content: '';
    position: absolute; top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
    border-radius: 50%;
}
.rw-hero::after {
    content: '';
    position: absolute; bottom: -60px; left: 25%;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(100,181,246,0.12) 0%, transparent 70%);
    border-radius: 50%;
}
.rw-hero-inner { position: relative; z-index: 1; }
.rw-brand-row { display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }
.rw-icon { font-size: 3em; filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3)); }
.rw-brand { font-size: 2.4em; font-weight: 800; letter-spacing: -1px; color: white; line-height: 1; }
.rw-brand span { color: #90caf9; }
.rw-hero-headline {
    font-size: 1.3em; font-weight: 600;
    line-height: 1.5; margin: 0 0 8px;
    color: rgba(255,255,255,0.95);
    max-width: 700px;
}
.rw-hero-sub {
    font-size: 0.97em; color: rgba(255,255,255,0.75);
    margin: 0 0 24px; line-height: 1.6; max-width: 620px;
}
.rw-hero-features {
    display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;
}
.rw-hf {
    background: rgba(255,255,255,0.13);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 24px; padding: 5px 14px;
    font-size: 0.82em; font-weight: 500; color: white;
}
.rw-impact-row {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
    margin-top: 24px; padding-top: 24px;
    border-top: 1px solid rgba(255,255,255,0.15);
}
.rw-impact {
    background: rgba(255,255,255,0.08);
    border-radius: 12px; padding: 10px 12px;
    border: 1px solid rgba(255,255,255,0.12);
}
.rw-impact-who { font-size: 0.75em; color: #90caf9; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.rw-impact-what { font-size: 0.85em; color: rgba(255,255,255,0.85); line-height: 1.4; }

/* ── WOW BUTTONS ─────────────────────────────────────────────────────── */
.rw-wow-section { margin: 14px 0 10px; }
.rw-wow-label { font-size: 0.78em; font-weight: 600; color: #666; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.rw-wow-btns { display: flex; gap: 8px; flex-wrap: wrap; }
.rw-wow-btn {
    padding: 8px 16px; border-radius: 8px; border: 1.5px solid;
    font-size: 0.83em; font-weight: 600; cursor: pointer;
    transition: all 0.15s; background: white; font-family: 'Inter', sans-serif;
}
.rw-wow-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }
.rw-wow-scam   { border-color: #d93025; color: #d93025; }
.rw-wow-scam:hover   { background: #d93025; color: white; }
.rw-wow-battery { border-color: #f57c00; color: #f57c00; }
.rw-wow-battery:hover { background: #f57c00; color: white; }
.rw-wow-water  { border-color: #0288d1; color: #0288d1; }
.rw-wow-water:hover  { background: #0288d1; color: white; }
.rw-wow-boot   { border-color: #7b1fa2; color: #7b1fa2; }
.rw-wow-boot:hover   { background: #7b1fa2; color: white; }
.rw-wow-urdu   { border-color: #1e8e3e; color: #1e8e3e; }
.rw-wow-urdu:hover   { background: #1e8e3e; color: white; }

/* ── CHAT AREA ───────────────────────────────────────────────────────── */
.rw-chat-wrap { display: flex; flex-direction: column; gap: 10px; }

/* ── PANELS ─────────────────────────────────────────────────────────── */
.rw-panel-wrap .label-wrap span { font-weight: 600 !important; }

/* ── SUBMIT BUTTON ──────────────────────────────────────────────────── */
.rw-submit-btn {
    background: linear-gradient(90deg, #1a73e8, #0d47a1) !important;
    font-weight: 700 !important; font-size: 1em !important;
    border-radius: 8px !important; letter-spacing: 0.02em !important;
}

/* ── FOOTER ─────────────────────────────────────────────────────────── */
.rw-footer {
    text-align: center; padding: 16px; font-size: 0.81em;
    color: #666; border-top: 1px solid #eee; margin-top: 12px;
}
.rw-footer a { color: #1a73e8; text-decoration: none; font-weight: 500; }
.rw-footer a:hover { text-decoration: underline; }

@media (max-width: 900px) {
    .rw-impact-row { grid-template-columns: repeat(2, 1fr); }
    .rw-brand { font-size: 1.8em; }
    .rw-hero-headline { font-size: 1.1em; }
}
"""


DEMO_BANNER_GPU = f"&nbsp;&nbsp;<span style='background:#fff3cd;color:#856404;padding:2px 10px;border-radius:12px;font-size:0.75em;font-weight:600'>GPU: HF Free Tier</span>" if DEMO_MODE else ""

with gr.Blocks(
    theme=gr.themes.Soft(
        primary_hue="blue",
        font=gr.themes.GoogleFont("Inter"),
    ),
    css=CSS,
    title="RepairWise Gemma — Phone Repair & Scam Safety AI",
) as demo:

    # ── HERO ──────────────────────────────────────────────────────────────
    gr.HTML(f"""
    <div class="rw-hero">
      <div class="rw-hero-inner">
        <div class="rw-brand-row">
          <span class="rw-icon">📱</span>
          <span class="rw-brand">RepairWise<span> Gemma</span></span>
          {DEMO_BANNER_GPU}
        </div>
        <p class="rw-hero-headline">
          AI safety &amp; repair for the next billion smartphone users.
        </p>
        <div class="rw-hero-features">
          <span class="rw-hf">🤖 Gemma 4 E2B · Unsloth</span>
          <span class="rw-hf">🔒 Fully offline</span>
          <span class="rw-hf">📸 Multimodal</span>
          <span class="rw-hf">💬 6 languages</span>
          <span class="rw-hf">🦁 Cactus router</span>
        </div>
        <div class="rw-impact-row">
          <div class="rw-impact">
            <div class="rw-impact-who">👴 Elderly</div>
            <div class="rw-impact-what">Avoid phishing scams safely</div>
          </div>
          <div class="rw-impact">
            <div class="rw-impact-who">🌍 Immigrants</div>
            <div class="rw-impact-what">Arabic · Urdu · Romanian</div>
          </div>
          <div class="rw-impact">
            <div class="rw-impact-who">🏘️ Rural</div>
            <div class="rw-impact-what">Works offline, no cloud</div>
          </div>
          <div class="rw-impact">
            <div class="rw-impact-who">🔐 Privacy</div>
            <div class="rw-impact-what">No data uploaded ever</div>
          </div>
        </div>
      </div>
    </div>

    """)

    # ── WOW BUTTONS — using Gradio native events (reliable in Gradio 5) ──

    # ── WOW BUTTONS ───────────────────────────────────────────────────────
    with gr.Group(elem_classes="rw-wow-strip"):
        gr.HTML('<div class="label">⚡ Quick scenarios — click to try instantly</div>')
        with gr.Row():
            btn_scam    = gr.Button("🚨 SMS Phishing (ES)", size="sm", elem_classes="rw-btn-scam")
            btn_battery = gr.Button("🔋 Batería hinchada (ES)", size="sm", elem_classes="rw-btn-battery")
            btn_water   = gr.Button("💧 Water damage (EN)", size="sm", elem_classes="rw-btn-water")
            btn_boot    = gr.Button("🔄 Boot issue (CA)", size="sm", elem_classes="rw-btn-boot")
            btn_urdu    = gr.Button("🌙 Scam SMS (UR)", size="sm", elem_classes="rw-btn-urdu")
            btn_arabic  = gr.Button("⚠️ بطارية منتفخة (AR)", size="sm", elem_classes="rw-btn-arabic")

    # ── MAIN LAYOUT ───────────────────────────────────────────────────────
    with gr.Row(equal_height=False):

        # ── LEFT: Chat + Input ────────────────────────────────────────
        with gr.Column(scale=5):
            gr.HTML("""
            <div style="
                border: 2px solid #e0e8ff;
                border-radius: 12px;
                background: #ffffff;
                padding: 12px;
                margin-bottom: 8px;
                box-shadow: 0 1px 6px rgba(26,115,232,0.08);
            ">
                <div style="font-size:11px;color:#1a73e8;font-weight:700;
                            text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px;">
                    💬 Conversation
                </div>
            </div>
            """)
            chatbot = gr.Chatbot(
                height=320, type="messages", show_label=False,
                placeholder=(
                    "## 👋 Welcome to RepairWise\n"
                    "Click a scenario button above, or describe your problem below.\n\n"
                    "**Supported:** Spanish · English · Catalan · Arabic · Romanian · Urdu"
                ),
            )

            # Visual divider + input label
            gr.HTML("""
            <div style="margin-top:10px;">
                <div style="
                    background: linear-gradient(90deg, #1a73e8, #0d47a1);
                    border-radius: 10px 10px 0 0;
                    padding: 10px 16px;
                    border: 2px solid #1a73e8;
                    border-bottom: none;
                ">
                    <span style="color:white; font-size:0.85em; font-weight:700; letter-spacing:0.05em;">
                        ✏️ DESCRIBE YOUR PROBLEM
                    </span>
                </div>
                <div style="
                    border: 2px solid #e0e8ff;
                    border-top: none;
                    border-radius: 0 0 10px 10px;
                    background: #f8faff;
                    padding: 2px;
                ">
            </div>
            """)

            # Input area with styled background
            with gr.Group():
                with gr.Row():
                    lang_drop = gr.Dropdown(
                        choices=["Spanish","English","Catalan","Arabic","Romanian","Urdu"],
                        value="Spanish",
                        label="🌍 Language",
                        scale=1, min_width=140,
                    )
                    txt_input = gr.Textbox(
                        placeholder="e.g. Me llegó un SMS del banco con un link sospechoso...",
                        lines=3, label="Your message", scale=4,
                    )

            with gr.Row():
                img_input = gr.Image(
                    label="📸 Photo (optional)",
                    type="numpy",
                    scale=2,
                    height=80,
                )
                with gr.Column(scale=3, min_width=140):
                    submit_btn = gr.Button(
                        "🔍 Analyse / Analizar",
                        variant="primary",
                        elem_classes="rw-submit-btn",
                        size="lg",
                    )
                    clear_btn = gr.Button("🗑 Clear", size="sm")

        # ── RIGHT: Technical panels ───────────────────────────────────
        with gr.Column(scale=4):
            gr.HTML("""
            <style>
            .rw-right-panel {
                border: 2px solid #e0e8ff !important;
                border-radius: 12px !important;
                overflow: hidden !important;
                box-shadow: 0 1px 6px rgba(26,115,232,0.08) !important;
            }
            </style>
            <div style="
                background: linear-gradient(90deg, #0d47a1, #1a73e8);
                border-radius: 10px 10px 0 0;
                padding: 10px 16px;
                margin-bottom: 0;
            ">
                <span style="color:white; font-size:0.85em; font-weight:700; letter-spacing:0.05em;">
                    🧠 AI ANALYSIS ENGINE
                </span>
            </div>
            """)
            with gr.Tabs():
                with gr.Tab("🧠 AI Decision System"):
                    judge_panel = gr.Textbox(
                        label="", lines=20, interactive=False,
                        show_copy_button=True,
                    )
                with gr.Tab("📚 Knowledge Sources"):
                    sources_out = gr.Textbox(
                        label="", lines=10, interactive=False,
                        placeholder="Knowledge sources used will appear here.",
                    )
                with gr.Tab("🔬 Model Reasoning"):
                    raw_out = gr.Textbox(
                        label="", lines=10, interactive=False,
                        placeholder=(
                            "Model reasoning appears here with GPU.\n\n"
                            "HF Free Tier: deterministic pipeline active.\n"
                            "See Kaggle notebook for Gemma 4 thinking mode."
                        ),
                    )

    # ── EXAMPLES (helps judges try scenarios instantly) ──────────────────
    if DEMO_MODE:
        gr.Examples(
            examples=DEMO_EXAMPLES,
            inputs=[txt_input, lang_drop],
            label="💡 Try these scenarios (click to load)",
            examples_per_page=5,
        )

    # ── FOOTER ────────────────────────────────────────────────────────────
    gr.HTML("""
    <div class="rw-footer">
      🔒 <strong>Privacy-first</strong> — No cloud API · No data stored · Fully offline via Ollama / llama.cpp / LiteRT
      &nbsp;·&nbsp;
      🤗 <a href="https://huggingface.co/abdullahfasih/repairwise-gemma4-e2b-lora">Fine-tuned model</a>
      &nbsp;·&nbsp;
      💻 <a href="https://github.com/SocAbdul/repairwise-gemma">GitHub</a>
      &nbsp;·&nbsp;
      Built for <strong>Gemma 4 Good Hackathon 2026</strong>
    </div>
    """)

    # ── EVENTS ────────────────────────────────────────────────────────────
    # WOW button events — fill input + set language
    btn_scam.click(
        fn=lambda: ("Me ha llegado un SMS del banco con un link y me pide la tarjeta y el PIN.", "Spanish"),
        outputs=[txt_input, lang_drop]
    )
    btn_battery.click(
        fn=lambda: ("Mi batería está hinchada y la pantalla se está levantando.", "Spanish"),
        outputs=[txt_input, lang_drop]
    )
    btn_water.click(
        fn=lambda: ("I dropped my phone in water and now it is getting very hot.", "English"),
        outputs=[txt_input, lang_drop]
    )
    btn_boot.click(
        fn=lambda: ("El meu mòbil no s'encén i es queda al logo.", "Catalan"),
        outputs=[txt_input, lang_drop]
    )
    btn_urdu.click(
        fn=lambda: ("مجھے بینک کا مشکوک پیغام آیا جس میں PIN مانگا گیا۔", "Urdu"),
        outputs=[txt_input, lang_drop]
    )
    btn_arabic.click(
        fn=lambda: ("بطارية هاتفي منتفخة والشاشة ترتفع عن الجسم.", "Arabic"),
        outputs=[txt_input, lang_drop]
    )

    submit_btn.click(
        fn=repairwise_chat,
        inputs=[txt_input, lang_drop, img_input, chatbot],
        outputs=[chatbot, judge_panel, sources_out, raw_out, txt_input],
    )
    txt_input.submit(
        fn=repairwise_chat,
        inputs=[txt_input, lang_drop, img_input, chatbot],
        outputs=[chatbot, judge_panel, sources_out, raw_out, txt_input],
    )
    # Note: Gradio 5 auto-detects generator functions and streams them
    clear_btn.click(fn=clear_chat, outputs=[chatbot, judge_panel, sources_out, raw_out, txt_input])

demo.launch()
