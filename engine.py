# RepairWise Gemma — Engine
# All core logic: triage, RAG, Gemma 4 generation, function calling, streaming
# Compatible with Kaggle (local paths) and Hugging Face Spaces (hub download)


# ============================================================
# RepairWise AI V13 Final Clean Engine
# ============================================================
# One clean definition per function. No V6→V12 monkey-patches remain.
# Core design: safety-first deterministic triage + local RAG + Gemma 4 enrichment/multimodal vision + guarded fallback.

import re
import json
import unicodedata
from typing import Optional, Any
import numpy as np
import threading
import time
from transformers import TextIteratorStreamer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from PIL import Image as PILImage
# ── Data pack imports (knowledge base + templates) ──────────────────────────
from data_pack import (
    LOCAL_KNOWLEDGE,
    CATEGORY_RESPONSE_TEMPLATES,
    PHOTO_VISUAL_CATEGORIES,
    SECTION_LABELS,
)
# Alias for backwards compatibility
LABELS = SECTION_LABELS


# ── Model globals (injected by app.py after loading) ─────────────────────────
# In Kaggle notebooks these are kernel globals. As a module they must be
# declared here and set by app.py before any generation call.
model = None
processor = None
DEMO_MODE = False  # Set to True by app.py if no GPU or model load fails

# ── Ollama backend ────────────────────────────────────────────────────────────
# RepairWise supports two backends:
#   1. HuggingFace Transformers (default, GPU required)
#   2. Ollama (local HTTP API, CPU/GPU, no Python GPU needed)
#
# To use Ollama:
#   1. Install: https://ollama.ai
#   2. Run: ollama pull gemma4:e2b
#   3. Set env: REPAIRWISE_BACKEND=ollama
#      Or:     OLLAMA_URL=http://localhost:11434

import os as _os
import urllib.request as _urllib_req
import json as _json

REPAIRWISE_BACKEND = _os.environ.get("REPAIRWISE_BACKEND", "transformers").lower()
OLLAMA_URL = _os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = _os.environ.get("OLLAMA_MODEL", "gemma4:e2b")

def _ollama_available() -> bool:
    """Check if Ollama server is running."""
    try:
        req = _urllib_req.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2)
        return req.status == 200
    except Exception:
        return False

def _ollama_chat(prompt: str, max_tokens: int = 220) -> str:
    """Call Ollama /api/generate endpoint with Gemma 4."""
    payload = _json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.4,
            "repeat_penalty": 1.12,
            "stop": ["<end_of_turn>", "<start_of_turn>"],
        }
    }).encode()
    try:
        req = _urllib_req.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urllib_req.urlopen(req, timeout=60) as resp:
            data = _json.loads(resp.read())
            return data.get("response", "").replace("<end_of_turn>", "").strip()
    except Exception as exc:
        return ""

def _ollama_stream(prompt: str, max_tokens: int = 220):
    """Stream tokens from Ollama — yields text chunks."""
    payload = _json.dumps({
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.4,
            "repeat_penalty": 1.12,
            "stop": ["<end_of_turn>", "<start_of_turn>"],
        }
    }).encode()
    try:
        req = _urllib_req.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urllib_req.urlopen(req, timeout=120) as resp:
            for line in resp:
                if line:
                    chunk = _json.loads(line)
                    token = chunk.get("response", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break
    except Exception:
        return

# Detect active backend at startup
_USE_OLLAMA = (REPAIRWISE_BACKEND == "ollama") or (
    REPAIRWISE_BACKEND == "auto" and _ollama_available()
)
if _USE_OLLAMA:
    print(f"✅ Ollama backend active: {OLLAMA_URL} | model: {OLLAMA_MODEL}")
else:
    print(f"ℹ️  Backend: transformers (HuggingFace)")
# ── llama.cpp backend ─────────────────────────────────────────────────────────
# RepairWise supports llama.cpp via its OpenAI-compatible server.
# Run: llama-server --model gemma-4-e2b.gguf --port 8080
# Then: REPAIRWISE_BACKEND=llamacpp python app.py
#
# llama.cpp enables running Gemma 4 E2B quantized (Q4_K_M ~1.5GB) on:
# - MacBook with Apple Silicon (Metal acceleration)
# - Any CPU with 8GB RAM
# - Raspberry Pi 5 (edge deployment)

LLAMACPP_URL  = _os.environ.get("LLAMACPP_URL", "http://localhost:8080")
LLAMACPP_MODEL = _os.environ.get("LLAMACPP_MODEL", "gemma-4-e2b")

def _llamacpp_available() -> bool:
    try:
        req = _urllib_req.urlopen(f"{LLAMACPP_URL}/health", timeout=2)
        return req.status == 200
    except Exception:
        return False

def _llamacpp_chat(prompt: str, max_tokens: int = 220) -> str:
    """Call llama.cpp OpenAI-compatible /v1/completions endpoint."""
    payload = _json.dumps({
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": 0.4,
        "repeat_penalty": 1.12,
        "stop": ["<end_of_turn>", "<start_of_turn>"],
        "stream": False,
    }).encode()
    try:
        req = _urllib_req.Request(
            f"{LLAMACPP_URL}/completion",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urllib_req.urlopen(req, timeout=120) as resp:
            data = _json.loads(resp.read())
            return data.get("content", "").replace("<end_of_turn>", "").strip()
    except Exception as exc:
        return ""

def _llamacpp_stream(prompt: str, max_tokens: int = 220):
    """Stream tokens from llama.cpp."""
    payload = _json.dumps({
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": 0.4,
        "repeat_penalty": 1.12,
        "stop": ["<end_of_turn>", "<start_of_turn>"],
        "stream": True,
    }).encode()
    try:
        req = _urllib_req.Request(
            f"{LLAMACPP_URL}/completion",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urllib_req.urlopen(req, timeout=120) as resp:
            for line in resp:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    chunk_str = line[6:]
                    if chunk_str == "[DONE]":
                        break
                    try:
                        chunk = _json.loads(chunk_str)
                        token = chunk.get("content", "")
                        if token:
                            yield token
                        if chunk.get("stop"):
                            break
                    except Exception:
                        pass
    except Exception:
        return

# Detect llama.cpp backend
_USE_LLAMACPP = (REPAIRWISE_BACKEND == "llamacpp") or (
    REPAIRWISE_BACKEND == "auto" and not _USE_OLLAMA and _llamacpp_available()
)
if _USE_LLAMACPP:
    print(f"✅ llama.cpp backend active: {LLAMACPP_URL}")




REPAIRWISE_VERSION = "V17 Real Streaming Final"
USE_GEMMA_TEXT_ENRICHMENT = True

LAST_GEMMA_TRACE = {
    "called": False,
    "path": "not_called",
    "raw": "",
    "fallback_used": False,
    "error": "",
    "function_calling": {
        "attempted": False,
        "native_tools_passed": False,
        "tool_name": "",
        "tool_args": {},
        "tool_result": {},
        "raw": "",
        "error": "",
    },
    "image_description": {
        "called": False,
        "raw": "",
        "error": "",
    },
    "streaming": {
        "enabled": False,
        "mode": "",
        "chunks": 0,
        "raw": "",
        "error": "",
    },
}

URGENCY_EMOJI = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}

LANGUAGE_INSTRUCTIONS = {
    "Spanish": "Responde completamente en español claro y práctico.",
    "English": "Answer completely in clear, practical English.",
    "Catalan": "Respon completament en català clar i pràctic.",
    "Urdu": "مکمل جواب اردو میں دیں، واضح اور عملی انداز میں۔",
    "Arabic": "أجب بالكامل باللغة العربية بشكل واضح وعملي.",
    "Romanian": "Răspunde complet în limba română, clar și practic.",
}

LANGUAGE_ALIASES = {
    "english": "English", "en": "English", "inglés": "English", "ingles": "English",
    "spanish": "Spanish", "es": "Spanish", "español": "Spanish", "espanol": "Spanish",
    "catalan": "Catalan", "ca": "Catalan", "català": "Catalan", "catala": "Catalan",
    "urdu": "Urdu", "ur": "Urdu",
    "arabic": "Arabic", "ar": "Arabic", "árabe": "Arabic", "arabe": "Arabic",
    "romanian": "Romanian", "ro": "Romanian", "rumano": "Romanian",
}

TEMPLATE_ALIASES = {
    "scam_data_entered": "scam_clicked_link",  # Uses clicked_link template + specific rec
    # scam_clicked_link has its own template in data_pack
    "network_issue": "sim_network_issue",
    "audio_issue": "speaker_microphone_issue",
    "speaker_microphone_issue": "speaker_microphone_issue",
    "online_service_issue": "app_issue",
    "software_issue": "update_issue",
    "image_analysis": "photo_unclear",
    "photo_unclear": "photo_unclear",
}

# Copy available same-language templates into aliases so coverage checks are honest.
for _lang, _templates in CATEGORY_RESPONSE_TEMPLATES.items():
    if "sim_network_issue" in _templates:
        _templates.setdefault("network_issue", _templates["sim_network_issue"])
    if "speaker_microphone_issue" in _templates:
        _templates.setdefault("audio_issue", _templates["speaker_microphone_issue"])
    if "app_issue" in _templates:
        _templates.setdefault("online_service_issue", _templates["app_issue"])
    if "update_issue" in _templates:
        _templates.setdefault("software_issue", _templates["update_issue"])
    _templates.setdefault("warranty", _templates.get("privacy_repair", _templates.get("unknown")))
    _templates.setdefault("faceid_touchid_issue", _templates.get("unknown"))

CATEGORY_PRIORITY = [
    "battery_safety", "scam_phishing", "water_damage", "sim_network_issue", "charging_issue",
    "app_issue", "wifi_issue", "bluetooth_issue", "overheating_issue", "storage_issue",
    "update_issue", "boot_issue", "screen_repair", "camera_issue", "faceid_touchid_issue",
    "audio_issue", "data_recovery", "privacy_repair", "warranty"
]

TEXT_GEMMA_ENRICH_CATEGORIES = {
    "charging_issue", "charging_port_issue", "sim_network_issue", "network_issue",
    "app_issue", "wifi_issue", "bluetooth_issue", "camera_issue", "screen_repair",
    "storage_issue", "update_issue", "faceid_touchid_issue", "speaker_microphone_issue",
    "audio_issue", "online_service_issue", "software_issue"
}

HIGH_RISK_CATEGORIES = {"scam_phishing", "battery_safety", "water_damage", "overheating_issue", "boot_issue", "data_recovery"}
MEDIUM_RISK_CATEGORIES = {"charging_issue", "charging_port_issue", "screen_repair", "camera_issue", "update_issue", "faceid_touchid_issue", "battery_drain", "audio_issue"}

DANGER_WATER_TERMS = [
    "water", "liquid", "moisture", "corrosion", "rust", "salt water",
    "agua", "liquido", "líquido", "humedad", "corrosion", "corrosión", "oxido", "óxido", "mojado", "mojada",
    "aigua", "mullat", "mullada", "humitat", "corrosio", "corrosió", "oxid", "òxid",
    "پانی", "گیلا", "نمی", "ماء", "رطوبة", "سائل", "apa", "lichid", "umezeala", "coroziune",
]
DANGER_BATTERY_TERMS = [
    "swollen battery", "battery swollen", "battery bulging", "screen lifting", "lifted screen",
    "bateria hinchada", "batería hinchada", "bateria inflada", "pantalla levantada",
    "bateria inflada", "pantalla aixecada", "بیٹری پھولی", "بطارية منتفخة", "baterie umflata",
]
DANGER_SCAM_TERMS = [
    # Core scam signals
    "phishing", "scam", "bank link", "otp", "card details", "suspicious link",
    "banco", "tarjeta", "codigo", "código", "enlace sospechoso",
    "banc", "targeta", "codi", "enllas", "enlac",
    "بینک", "کارڈ", "کوڈ", "رابطہ", "بنك", "بطاقة", "رمز", "رابط",
    "banca", "card", "cod", "link",
    # Clicked phishing link — various forms and typos
    "abri el enlace", "abrí el enlace", "abri el link",
    "he abierto", "abierto el enlace", "abierto el link",
    "hice clic", "pulsé el link", "cliqué", "pinché el link",
    "opened the link", "clicked the link", "i clicked", "i opened",
    "abrí el enlace", "abri enlace",
    # Typo-tolerant (common mistakes)
    "abri el enclace", "abri el enlance", "abrí el enclace",
    "he abierto el enclace", "he abierto enclace",
    # Catalan
    "he obert l", "vaig clicar", "he fet clic",
    # Romanian
    "am deschis", "am dat click",
    # Urdu/Arabic
    "لنک کھولا", "لنک پر کلک", "فتحت الرابط", "ضغطت على الرابط",
]

SIGNAL_NETWORK_PATTERNS = [
    r"\b(no|not|without)\s+(signal|service|coverage|network)\b",
    r"\b(signal|service|coverage|network)\s+(not working|problem|issue|gone|lost)\b",
    r"\bemergency\s+calls?\s+only\b",
    r"\b(no|not)\s+detect(?:ing)?\s+sim\b",
    r"\bsim\s+(not detected|not working|problem|issue)\b",
    r"\bmobile\s+data\s+(not working|problem|issue)\b",
    r"\b(no|sin)\s+(senal|senyal|cobertura|servicio|red)\b",
    r"\b(no tengo|no hay|no coge|no agarra|no pilla)\s+(senal|cobertura|red)\b",
    r"\bsolo\s+(emergencia|llamadas de emergencia)\b",
    r"\bsim\s+(no detecta|no funciona|sin servicio)\b",
    r"\b(no|sense)\s+(cobertura|senyal|xarxa|servei)\b",
    r"\b(no te|no tinc|no hi ha|no agafa|no pilla)\s+(cobertura|senyal|xarxa)\b",
    r"\bdades\s+mobils\s+(no funcionen|no va|fallen)\b",
    r"(signal|network|sim).*(nahi|nahin|not)",
    r"(سگنل|نیٹ ورک|سم).*(نہیں|مسئلہ|خراب)",
    r"(اشارة|شبكة|شريحة|sim).*(لا|مشكلة|لا تعمل)",
    r"\b(fara|nu are|nu am)\s+(semnal|retea|acoperire|serviciu)\b",
]
CHARGING_PATTERNS = [
    r"\b(not charging|doesnt charge|doesn t charge|won t charge|no charge)\b",
    r"\b(no carga|no carrega|no se carga|no es carrega)\b",
    r"\b(charging port|puerto de carga|port de carrega|usb c|lightning)\b",
    r"\b(only charges at angle|solo carga.*muevo|carga.*angulo|carrega.*angle)\b",
]
APP_PATTERNS = [
    r"\b(whatsapp|whastapp|watsapp|whatsap|wasap|instagram|tiktok|facebook|telegram|gmail|youtube)\b",
    r"\b(app|aplicacion|aplicacio|application)\s+(no funciona|not working|no va|se cierra|crash)\b",
]
WIFI_PATTERNS = [r"\b(wifi|wi fi|router|dns)\b.*\b(no|not|problem|issue|disconnect|slow|lento|no conecta|no connecta)\b"]
BLUETOOTH_PATTERNS = [r"\b(bluetooth|airpods|auriculares)\b.*\b(no|not|problem|issue|connect|conecta|empareja)\b"]
STORAGE_PATTERNS = [r"\b(storage full|low storage|memory full|almacenamiento lleno|memoria llena|espai ple|emmagatzematge)\b"]
UPDATE_PATTERNS = [r"\b(update failed|ios update|android update|actualizacion|actualització|stuck updating)\b"]
BATTERY_DRAIN_PATTERNS = [
    r"\b(battery.*(drain|drains|draining|dies fast|runs out|doesn.?t last|not lasting|last long|doent|doesnt|doenst))\b",
    r"\b(battery.*(long|hold|enough|charge|go|last).*(not|no|dont|doesnt|doent|wont))\b",
    r"\b(phone.*(battery|charge).*(dies|dead|gone|low).*(fast|quick|soon|hour|minute))\b",
    r"\b(battery.*(percentage|life|health).*(low|bad|poor|worse))\b",
    r"\b(se.*(gasta|agota|acaba).*(rapido|rápido|pronto|enseguida))\b",
    r"\b(bateria.*(dura|aguanta|no.?dura|poca|poca duración))\b",
    r"\b(battery.*(30|20|10).*(percent|%|minutes|hour))\b",
]

BOOT_PATTERNS = [
    r"\b(bootloop|boot.?loop|stuck.?on.?logo|stuck.?logo|not turning on|won.?t turn on|wont turn on|won t turn on)\b",
    r"\bno\s+(se\s+|me\s+)?enciende\b|\bno\s+(se\s+)?arranca\b|\bno\s+(se\s+)?prende\b|\breinicia en bucle\b|\bse queda en el logo\b|\batascado en logo\b",
    r"\b(no s.?enc[eé]n|no se encen|no s encen|encen|no engega|no arrenca|es queda al logo|bloquejat al logo|no s.?encen)\b",
    r"\b(nu porneste|blocat pe logo|reporneste singur|nu se opreste)\b",
    r"(band hogaya|bandho gaya|on nahi|nahi chalu|nahi chalta|start nahi|logo pe atka|nahi chal raha)\b",
    r"(بند ہوگیا|آن نہیں|لوگو پر|اسٹارٹ نہیں)",
    r"(لا يعمل|علق عند الشعار|يعيد التشغيل|لا يفتح)",
]
SCREEN_PATTERNS = [r"\b(screen|pantalla|display|oled|lcd|green line|linea verde|línea verde|touch)\b.*\b(broken|cracked|rota|negra|black|line|flicker|no responde)\b"]
CAMERA_PATTERNS = [r"\b(camera|camara|cámara|camera lens|lente)\b.*\b(black|negra|blurry|borrosa|focus|enfoque|shake|vibra)\b"]
AUDIO_PATTERNS = [
    r"\b(se escucha|se oye|se escuha)\s*(muy\s*)?(flojo|bajo|poco|mal|raro|distorsionado)\b",
    r"\b(muy\s*)?(flojo|bajo|poco)\s*(volumen|sonido|audio)\b",
    r"\b(volumen|volume)\s*(bajo|low|flojo|too low|very low)\b",
    r"\b(speaker|microphone|mic|altavoz|microfono|micrófono|audio|sound|sonido)\b.*\b(no|not|problem|issue|funciona|hear|escucha)\b",
    r"\b(no (escucho|oigo|se escucha|se oye)|sonido (no|mal|roto)|audio (falla|no))\b",
    r"\b(so no funciona|auricular|earpiece|earbud)\b",
]
FACEID_PATTERNS = [r"\b(face id|faceid|touch id|touchid|fingerprint|huella|biometric|biometrico|biometric)\b"]
OVERHEAT_PATTERNS = [r"\b(overheating|phone hot|very hot|gets hot|se calienta|caliente|s'escalfa|fierbinte|burning smell|olor raro)\b"]
DATA_PATTERNS = [r"\b(recover photos|recover data|data recovery|recuperar fotos|recuperar datos|dades|backup|whatsapp backup)\b"]
PRIVACY_PATTERNS = [r"\b(privacy|privacidad|privacitat|passcode|password|contraseña|contrasenya|repair access|datos personales)\b"]

PHOTO_VISUAL_CATEGORIES = {
    "photo_screen_crack": {
        "repair_category": "screen_repair", "risk": "MEDIUM",
        "sources": ["photo_screen_crack_display", "photo_visual_inspection_external"],
        "keywords": ["cracked screen", "broken glass", "green line", "black display", "pantalla rota", "línea verde"],
    },
    "photo_battery_swelling": {
        "repair_category": "battery_safety", "risk": "HIGH",
        "sources": ["photo_battery_swelling_lifted_screen", "battery_swollen_safety"],
        "keywords": ["lifted screen", "swollen battery", "back cover lifted", "pantalla levantada", "batería hinchada"],
    },
    "photo_charging_port": {
        "repair_category": "charging_port_issue", "risk": "MEDIUM",
        "sources": ["photo_charging_port_damage", "charging_port_dirty_loose"],
        "keywords": ["charging port", "usb c", "lightning", "puerto de carga", "conector carga"],
    },
    "photo_water_corrosion": {
        "repair_category": "water_damage", "risk": "HIGH",
        "sources": ["photo_water_corrosion_visible", "water_damage_salt_corrosion"],
        "keywords": ["corrosion", "water damage", "liquid", "moisture", "agua", "humedad", "óxido", "corrosión"],
    },
    "photo_scam_screenshot": {
        "repair_category": "scam_phishing", "risk": "HIGH",
        "sources": ["photo_scam_sms_screenshot", "scam_bank_sms_privacy"],
        "keywords": ["sms", "bank", "link", "card", "otp", "pin", "password", "banco", "tarjeta", "codigo"],
    },
    "photo_app_error_screenshot": {
        "repair_category": "app_issue", "risk": "LOW",
        "sources": ["photo_app_error_screenshot", "app_whatsapp_not_working", "storage_full_app_system"],
        "keywords": ["whatsapp", "instagram", "tiktok", "app error", "login", "no funciona", "se cierra"],
    },
    "photo_camera_lens": {
        "repair_category": "camera_issue", "risk": "MEDIUM",
        "sources": ["photo_camera_lens_damage", "camera_black_blurry_permissions"],
        "keywords": ["camera lens", "lens cracked", "camera glass", "cámara", "lente", "foto borrosa"],
    },
    "photo_unclear": {
        "repair_category": "photo_unclear", "risk": "LOW",
        "sources": ["photo_unclear_quality", "photo_visual_inspection_external"],
        "keywords": ["unclear photo", "blurry", "dark", "low resolution", "foto borrosa", "imagen oscura"],
    },
}

def reset_gemma_trace():
    LAST_GEMMA_TRACE.update({
        "called": False,
        "path": "not_called",
        "raw": "",
        "fallback_used": False,
        "error": "",
        "function_calling": {
            "attempted": False,
            "native_tools_passed": False,
            "tool_name": "",
            "tool_args": {},
            "tool_result": {},
            "raw": "",
            "error": "",
        },
        "image_description": {
            "called": False,
            "raw": "",
            "error": "",
        },
        "streaming": {
            "enabled": False,
            "mode": "",
            "chunks": 0,
            "raw": "",
            "error": "",
        },
    })

def normalize_language_name(language: str | None) -> str:
    if not language:
        return "Spanish"
    l = str(language).strip().lower()
    return LANGUAGE_ALIASES.get(l, language if language in LABELS else "Spanish")

def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text or ""))
    return "".join(ch for ch in text if not unicodedata.combining(ch))

def norm_text(text: str) -> str:
    text = strip_accents(text).lower()
    text = re.sub(r"[^a-z0-9\u0600-\u06FF\s]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()

def contains_any(text: str, terms: list[str]) -> bool:
    t = norm_text(text)
    return any(norm_text(term) in t for term in terms)

def matches_any(text: str, patterns: list[str]) -> bool:
    t = norm_text(text)
    return any(re.search(pattern, t, flags=re.IGNORECASE) for pattern in patterns)

def is_vague_problem(text: str) -> bool:
    t = norm_text(text)
    if not t:
        return True
    # Never treat these as vague — they have specific meaning
    specific_signals = [
        "encen", "enciende", "arranca", "prende", "engega", "start", "band hogaya", "hogaya",  # boot
        "carga", "carrega", "charging",  # charging
        "pantalla", "screen", "display",  # screen
        "agua", "water", "mojado",  # water
        "caliente", "hot", "escalfa",  # heat
        "sim", "cobertura", "senyal", "senal", "signal",  # network
    ]
    if any(s in t for s in specific_signals):
        return False
    if len(t.split()) <= 6 and re.search(r"\b(phone|movil|mobile|telefono|teléfono|mòbil|mobil)?\s*(no funciona|not working|doesnt work|doesn t work|va mal|problem|problema|no va)\b", t):
        return True
    return t in {"no funciona", "not working", "problema", "problem"}

def urgency_for_category(category: str) -> str:
    if category in HIGH_RISK_CATEGORIES:
        return "HIGH"
    if category in MEDIUM_RISK_CATEGORIES:
        return "MEDIUM"
    return "LOW"

def triage_issue(text: str, conversation_history: list | None = None) -> dict:
    # HIGH-PRIORITY checks run BEFORE vague gate — these are always actionable
    if contains_any(text, DANGER_BATTERY_TERMS):
        return {"urgency": "HIGH", "category": "battery_safety", "reason": "Explicit swollen battery/safety signal.", "method": "priority_battery", "confidence": 0.99}
    if contains_any(text, DANGER_SCAM_TERMS):
        t_n = norm_text(text)
        # Data entered → EMERGENCY escalation
        entered_words = ["puse", "pusé", "puse mis datos", "puse la tarjeta",
                         "puse el codigo", "introduje", "rellené", "entered",
                         "gave", "provided", "put my", "metí", "meti",
                         "he puesto", "puse datos", "puse el pin",
                         "he dado", "di mis datos", "put in my card",
                         "put my card", "filled in"]
        if any(w in t_n for w in entered_words):
            return {"urgency": "HIGH", "category": "scam_data_entered",
                    "reason": "EMERGENCY: User entered data on phishing site.",
                    "method": "priority_scam_data", "confidence": 0.99}
        # Clicked link
        clicked_words = ["abri", "abierto", "clic", "click", "puls", "pinch",
                         "opened", "clicked", "clique", "vaig clicar", "he obert",
                         "deschis", "dat click", "لنک کھولا", "فتحت"]
        if any(w in t_n for w in clicked_words):
            return {"urgency": "HIGH", "category": "scam_clicked_link",
                    "reason": "User clicked/opened phishing link.",
                    "method": "priority_scam_clicked", "confidence": 0.99}
        return {"urgency": "HIGH", "category": "scam_phishing",
                "reason": "Explicit phishing/scam signal.", "method": "priority_scam", "confidence": 0.98}
    # Water damage — check NEGATION first ("no se ha mojado", "nunca mojado")
    _t_water = norm_text(text)
    _negation = any(neg in _t_water for neg in [
        "no se ha mojado", "no se mojo", "nunca mojado", "nunca se mojo",
        "not wet", "never wet", "no ha caido", "no cayo al agua",
        "no entro agua", "hasn t been wet", "was not wet", "never dropped",
        "no s ha mullat", "no esta mojado",
    ])
    if not _negation and contains_any(text, DANGER_WATER_TERMS):
        return {"urgency": "HIGH", "category": "water_damage", "reason": "Explicit liquid/water/corrosion signal.", "method": "priority_water", "confidence": 0.98}
    # Vague gate runs AFTER high-priority scam/battery/water checks
    if is_vague_problem(text):
        return {"urgency": "LOW", "category": "vague_problem", "reason": "Vague problem; ask targeted repair questions.", "method": "v13_vague_gate", "confidence": 0.99}
    # Universal context inheritance — works for ALL 23 categories
    if conversation_history:
        inherited = detect_conversation_context(text, conversation_history, "Spanish")
        if inherited:
            # Special case: clicked phishing link gets specific category
            t_norm = norm_text(text)
            if inherited.get("category") in {"scam_phishing", "scam_clicked_link"}:
                clicked = any(x in t_norm for x in [
                    "abri", "clic", "click", "pulse", "entre",
                    "pinche", "open", "hice", "abrí", "opened", "clicked"
                ])
                if clicked:
                    inherited["category"] = "scam_clicked_link"
            return inherited

    checks = [
        ("sim_network_issue", SIGNAL_NETWORK_PATTERNS, 0.99),
        ("charging_issue", CHARGING_PATTERNS, 0.97),
        ("app_issue", APP_PATTERNS, 0.97),
        ("wifi_issue", WIFI_PATTERNS, 0.92),
        ("bluetooth_issue", BLUETOOTH_PATTERNS, 0.92),
        ("overheating_issue", OVERHEAT_PATTERNS, 0.94),
        ("battery_drain", BATTERY_DRAIN_PATTERNS, 0.93),
        ("storage_issue", STORAGE_PATTERNS, 0.90),
        ("update_issue", UPDATE_PATTERNS, 0.90),
        ("boot_issue", BOOT_PATTERNS, 0.90),
        ("screen_repair", SCREEN_PATTERNS, 0.90),
        ("camera_issue", CAMERA_PATTERNS, 0.88),
        ("audio_issue", AUDIO_PATTERNS, 0.88),
        ("faceid_touchid_issue", FACEID_PATTERNS, 0.88),
        ("data_recovery", DATA_PATTERNS, 0.88),
        ("privacy_repair", PRIVACY_PATTERNS, 0.86),
    ]
    for cat, patterns, conf in checks:
        if matches_any(text, patterns):
            return {"urgency": urgency_for_category(cat), "category": cat, "reason": f"High-precision pattern matched {cat}.", "method": "priority_pattern", "confidence": conf}
    cat, score = classify_semantic_category(text)
    return {"urgency": urgency_for_category(cat), "category": cat, "reason": f"Hybrid semantic classifier selected {cat}.", "method": "hybrid_tfidf_char", "confidence": float(score)}

def build_doc_text(doc: dict) -> str:
    parts = [doc.get("id", ""), doc.get("category", ""), doc.get("topic", ""), " ".join(doc.get("aliases", [])), doc.get("text", "")]
    return " ".join(str(p) for p in parts if p)

def canonical_category(category: str) -> str:
    return TEMPLATE_ALIASES.get(category, category)

CATEGORY_PROTOTYPES = {}
for _doc in LOCAL_KNOWLEDGE:
    CATEGORY_PROTOTYPES.setdefault(_doc["category"], [])
    CATEGORY_PROTOTYPES[_doc["category"]].append(build_doc_text(_doc))
CATEGORY_PROTOTYPES.update({
    "sim_network_issue": "no signal no service no coverage sim not detected apn emergency calls sin cobertura sense cobertura no te cobertura senyal xarxa dades mobils",
    "vague_problem": "mobile phone not working no funciona problema general pantalla carga bateria senal app camara sonido",
    "photo_unclear": "unclear blurry dark low resolution photo ask better image",
})


ALLOW_REMOTE_EMBEDDING_MODEL = True  # HF Spaces: download from hub
EMBEDDING_AVAILABLE = False
EMBEDDING_ERROR = ""
EMBEDDER = None
EMBED_MATRIX = None

def build_embedding_model_candidates() -> list[str]:
    """Local-first candidates for sentence-transformer semantic retrieval."""
    candidates = [
        "/kaggle/input/sentence-transformers-all-minilm-l6-v2",
        "/kaggle/input/all-minilm-l6-v2",
        "/kaggle/input/all-MiniLM-L6-v2",
        "/kaggle/input/bge-small-en-v15",
        "/kaggle/input/baai-bge-small-en-v1-5",
    ]
    if ALLOW_REMOTE_EMBEDDING_MODEL:
        candidates.extend([
            "sentence-transformers/all-MiniLM-L6-v2",
            "BAAI/bge-small-en-v1.5",
        ])
    return candidates

def try_init_semantic_retriever():
    """Optional semantic retriever using sentence-transformers.

    This is local-first and never breaks the notebook. If the embedding model is
    not available in the Kaggle runtime, RepairWise falls back to TF-IDF + char
    n-grams + keyword aliases.
    """
    global EMBEDDING_AVAILABLE, EMBEDDING_ERROR, EMBEDDER, EMBED_MATRIX
    EMBEDDING_AVAILABLE = False
    EMBEDDING_ERROR = ""
    EMBEDDER = None
    EMBED_MATRIX = None

    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:
        EMBEDDING_ERROR = f"sentence-transformers not available: {type(exc).__name__}: {exc}"
        return

    last_error = ""
    for candidate in build_embedding_model_candidates():
        try:
            # Skip non-existing local candidates.
            if candidate.startswith("/kaggle/input") and not os.path.exists(candidate):
                continue
            device = "cuda" if "torch" in globals() and torch.cuda.is_available() else "cpu"
            EMBEDDER = SentenceTransformer(candidate, device=device)
            EMBED_MATRIX = EMBEDDER.encode(
                DOC_TEXTS,
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
            EMBEDDING_AVAILABLE = True
            EMBEDDING_ERROR = ""
            print(f"✅ Semantic embedding retriever loaded: {candidate}")
            return
        except Exception as exc:
            last_error = f"{candidate}: {type(exc).__name__}: {exc}"

    EMBEDDING_ERROR = last_error or "No local embedding model candidate found."

def rebuild_repairwise_indexes():
    global DOC_TEXTS, WORD_VECTORIZER, CHAR_VECTORIZER, WORD_MATRIX, CHAR_MATRIX, CATEGORY_VECTORIZER, CATEGORY_MATRIX, CATEGORY_NAMES
    DOC_TEXTS = [build_doc_text(d) for d in LOCAL_KNOWLEDGE]
    WORD_VECTORIZER = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, strip_accents="unicode")
    CHAR_VECTORIZER = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), lowercase=True, strip_accents="unicode")
    WORD_MATRIX = WORD_VECTORIZER.fit_transform(DOC_TEXTS)
    CHAR_MATRIX = CHAR_VECTORIZER.fit_transform(DOC_TEXTS)
    CATEGORY_NAMES = sorted(CATEGORY_PROTOTYPES.keys())
    cat_texts = [" ".join(v) if isinstance(v, list) else str(v) for v in (CATEGORY_PROTOTYPES[c] for c in CATEGORY_NAMES)]
    CATEGORY_VECTORIZER = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, strip_accents="unicode")
    CATEGORY_MATRIX = CATEGORY_VECTORIZER.fit_transform(cat_texts)
    try_init_semantic_retriever()

def semantic_embedding_scores(queries: list[str]) -> np.ndarray:
    """Return max semantic score per doc from optional embedding retriever."""
    if not EMBEDDING_AVAILABLE or EMBEDDER is None or EMBED_MATRIX is None:
        return np.zeros(len(LOCAL_KNOWLEDGE), dtype=float)
    try:
        q_emb = EMBEDDER.encode(
            queries,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        sims = np.matmul(q_emb, EMBED_MATRIX.T)
        return np.max(sims, axis=0)
    except Exception as exc:
        # Keep notebook robust: semantic retrieval is optional.
        return np.zeros(len(LOCAL_KNOWLEDGE), dtype=float)


def classify_semantic_category(text: str) -> tuple[str, float]:
    q = CATEGORY_VECTORIZER.transform([text])
    scores = cosine_similarity(q, CATEGORY_MATRIX)[0]
    idx = int(np.argmax(scores))
    score = float(scores[idx])
    return (CATEGORY_NAMES[idx] if score >= 0.05 else "unknown", score)

def expand_repair_query(text: str, category: str) -> list[str]:
    base = text or ""
    expansions = {
        "sim_network_issue": "no signal no service coverage SIM APN emergency calls antenna carrier",
        "network_issue": "no signal no service coverage SIM APN emergency calls antenna carrier",
        "charging_issue": "not charging charger cable charging port USB-C Lightning battery",
        "charging_port_issue": "charging port dirty loose damaged USB-C Lightning connector",
        "app_issue": "app crash cache update storage internet WhatsApp Instagram TikTok login",
        "wifi_issue": "wifi router DNS network password disconnecting internet",
        "bluetooth_issue": "bluetooth pairing AirPods accessory disconnecting",
        "battery_safety": "swollen battery overheating screen lifting safety stop charging",
        "water_damage": "liquid water moisture corrosion salt water do not charge",
        "screen_repair": "screen display touch OLED LCD cracked black green line",
        "camera_issue": "camera black blurry focus lens permission module",
        "audio_issue": "speaker microphone call audio bluetooth voice recorder",
        "speaker_microphone_issue": "speaker microphone call audio bluetooth voice recorder",
        "scam_phishing": "SMS bank link card OTP password phishing scam",
        "data_recovery": "recover photos WhatsApp backup data restore",
        "storage_issue": "storage full memory full app crash update failed",
        "update_issue": "software update failed stuck logo bootloop",
        "faceid_touchid_issue": "Face ID Touch ID fingerprint biometric sensor",
    }
    out = [base]
    if category in expansions:
        out.append(base + " " + expansions[category])
    out.append(norm_text(base))
    return list(dict.fromkeys([x.strip() for x in out if x and x.strip()]))

def normalize_scores(scores: np.ndarray) -> np.ndarray:
    scores = np.array(scores, dtype=float)
    if len(scores) == 0:
        return scores
    max_s = float(np.max(scores))
    if max_s <= 0:
        return np.zeros_like(scores)
    return scores / max_s

def keyword_overlap_scores(queries: list[str]) -> np.ndarray:
    scores = np.zeros(len(LOCAL_KNOWLEDGE), dtype=float)
    query_text = " ".join(norm_text(q) for q in queries)
    for i, doc in enumerate(LOCAL_KNOWLEDGE):
        aliases = [doc.get("category", ""), doc.get("id", ""), doc.get("topic", "")] + doc.get("aliases", [])
        for alias in aliases:
            a = norm_text(alias)
            if a and a in query_text:
                scores[i] += 1.0
        for token in set(query_text.split()):
            if len(token) >= 4 and token in norm_text(build_doc_text(doc)):
                scores[i] += 0.05
    return scores

def allowed_doc_for_text(doc: dict, category: str, user_text: str, image_present: bool) -> bool:
    sid = str(doc.get("id", ""))
    dcat = doc.get("category", "")
    if not image_present and (sid.startswith("photo_") or dcat in {"image_analysis", "photo_unclear"}):
        return False
    if category in {"sim_network_issue", "network_issue"} and not contains_any(user_text, DANGER_WATER_TERMS):
        if dcat == "water_damage" or "water" in sid.lower() or "corrosion" in sid.lower():
            return False
    if category == "app_issue" and dcat in {"water_damage", "battery_safety", "boot_issue"}:
        return False
    if category in {"charging_issue", "charging_port_issue"} and dcat == "water_damage" and not contains_any(user_text, DANGER_WATER_TERMS):
        return False
    return True


def retrieve_knowledge(query: str, k: int = 5, category: str = "unknown", image_present: bool = False) -> list[dict]:
    """Hybrid local RAG.

    Engines:
    - word TF-IDF
    - character n-grams for typos
    - keyword/alias overlap
    - optional sentence-transformer embeddings

    Scores are combined as an ensemble, then category-aware reranking and
    source filtering are applied.
    """
    queries = expand_repair_query(query, category)
    word_scores_all, char_scores_all = [], []
    for q in queries:
        word_scores_all.append(cosine_similarity(WORD_VECTORIZER.transform([q]), WORD_MATRIX)[0])
        char_scores_all.append(cosine_similarity(CHAR_VECTORIZER.transform([q]), CHAR_MATRIX)[0])

    word_scores = np.max(np.vstack(word_scores_all), axis=0)
    char_scores = np.max(np.vstack(char_scores_all), axis=0)
    keyword_scores = keyword_overlap_scores(queries)
    semantic_scores = semantic_embedding_scores(queries)

    word_norm = normalize_scores(word_scores)
    char_norm = normalize_scores(char_scores)
    keyword_norm = normalize_scores(keyword_scores)
    semantic_norm = normalize_scores(semantic_scores)

    if EMBEDDING_AVAILABLE:
        scores = 0.30 * word_norm + 0.22 * char_norm + 0.18 * keyword_norm + 0.30 * semantic_norm
    else:
        scores = 0.42 * word_norm + 0.34 * char_norm + 0.24 * keyword_norm

    can = canonical_category(category)
    for i, doc in enumerate(LOCAL_KNOWLEDGE):
        dcat_can = canonical_category(doc.get("category", ""))
        if dcat_can == can or doc.get("category") == category:
            scores[i] += 0.25
        elif category != "unknown":
            scores[i] -= 0.06

    if category in HIGH_RISK_CATEGORIES:
        for i, doc in enumerate(LOCAL_KNOWLEDGE):
            if canonical_category(doc.get("category")) == can:
                scores[i] += 0.15

    order = np.argsort(scores)[::-1]
    docs = []
    for idx in order:
        if len(docs) >= k:
            break
        doc = dict(LOCAL_KNOWLEDGE[int(idx)])
        if not allowed_doc_for_text(doc, category, query, image_present):
            continue
        doc["score"] = float(max(scores[int(idx)], 0.0))
        doc["engine_scores"] = {
            "word": round(float(word_norm[int(idx)]), 3),
            "char": round(float(char_norm[int(idx)]), 3),
            "keyword": round(float(keyword_norm[int(idx)]), 3),
            "semantic": round(float(semantic_norm[int(idx)]), 3),
            "semantic_available": bool(EMBEDDING_AVAILABLE),
        }
        docs.append(doc)

    # Category relevance boost — matching docs rank higher, off-category penalized
    # Treat scam sub-categories as scam_phishing for RAG purposes
    rag_category = "scam_phishing" if category == "scam_clicked_link" else category
    if rag_category and docs and rag_category not in {"unknown", "vague_problem", "photo_unclear"}:
        matching = []
        others = []
        for _d in docs:
            _d = dict(_d)
            if _d.get("category") == category:
                _d["score"] = float(_d.get("score", 0)) * 2.0
                matching.append(_d)
            else:
                _d["score"] = float(_d.get("score", 0)) * 0.65
                others.append(_d)
        # Sort each group by score
        matching.sort(key=lambda d: float(d.get("score", 0)), reverse=True)
        others.sort(key=lambda d: float(d.get("score", 0)), reverse=True)
        # Matching docs first, then best non-matching to fill slots
        docs = matching + others

    return docs


def is_context_sufficient(docs: list[dict], category: str, min_score: float = 0.18) -> bool:
    if category in {"vague_problem", "unknown"}:
        return False
    if not docs:
        return False
    can = canonical_category(category)
    same = [d for d in docs[:3] if canonical_category(d.get("category", "")) == can and d.get("score", 0) >= min_score]
    return bool(same) or docs[0].get("score", 0) >= 0.35

def get_template_content(language: str, category: str) -> dict:
    lang = normalize_language_name(language)
    templates = CATEGORY_RESPONSE_TEMPLATES.get(lang, CATEGORY_RESPONSE_TEMPLATES["English"])
    cat = canonical_category(category)
    return templates.get(category) or templates.get(cat) or templates.get("unknown") or CATEGORY_RESPONSE_TEMPLATES["English"]["unknown"]

def risk_for_category(category: str, triage: dict | None = None) -> str:
    if triage and triage.get("urgency") in {"HIGH", "MEDIUM", "LOW"}:
        urg = triage["urgency"]
    else:
        urg = urgency_for_category(category)
    return f"{urg} {URGENCY_EMOJI.get(urg, '')}".strip()

def format_sources(docs: list[dict], category: str, user_text: str = "", image_present: bool = False) -> str:
    can = canonical_category(category)
    ids = []
    for d in docs or []:
        if not allowed_doc_for_text(d, category, user_text, image_present):
            continue
        if canonical_category(d.get("category", "")) != can and d.get("category") != category:
            continue
        sid = d.get("id")
        if sid and sid not in ids:
            ids.append(sid)
    defaults = {
        "sim_network_issue": ["network_sim_signal_apn"],
        "network_issue": ["network_sim_signal_apn"],
        "charging_issue": ["charging_port_basic", "charging_port_dirty_loose"],
        "charging_port_issue": ["charging_port_basic", "charging_port_dirty_loose"],
        "app_issue": ["app_whatsapp_not_working", "storage_full_app_system"],
        "vague_problem": ["vague_problem_safe_triage", "basic_phone_checks"],
        "unknown": ["safe_general_triage", "basic_phone_checks"],
        "photo_unclear": ["photo_unclear_quality", "photo_visual_inspection_external"],
    }
    if not ids:
        ids = defaults.get(category, defaults.get(can, ["safe_repair_triage", "basic_phone_checks"]))
    return "[" + ", ".join(ids[:3]) + "]"

def safe_fallback_answer(user_text: str, triage: dict, docs: list, language: str = "Spanish", image_present: bool = False) -> str:
    lang = normalize_language_name(language)
    labels = LABELS.get(lang, LABELS["Spanish"])
    category = (triage or {}).get("category", "unknown")
    template = get_template_content(lang, category)
    risk = risk_for_category(category, triage)
    sources = format_sources(docs, category, user_text, image_present=image_present)
    recommendation = get_recommendation(category, lang)
    # Recommendation section label per language
    _rec_labels = {
        "Spanish": "Recomendación",
        "English": "Recommendation",
        "Catalan": "Recomanació",
        "Arabic":  "التوصية",
        "Romanian":"Recomandare",
        "Urdu":    "سفارش",
    }
    rec_label = _rec_labels.get(lang, "3. Recommendation")
    return (
        f"1. {labels[0]}: {template['diagnosis']}\n"
        f"2. {labels[1]}: {risk}  \n   ⚡ **{rec_label}**: {recommendation}  \n"
        f"3. {labels[2]}: {template['action']}\n"
        f"4. {labels[3]}: {template['visit']}\n"
        f"5. {labels[4]}: {sources}"
    )

INTERNAL_LEAK_MARKERS = [
    "system prompt", "hidden context", "knowledge base", "customer message:", "local repair context:",
    "modelar:", "interno:", "biométrico:", "touch id:", "fingerprint:", "sensor:", "screen protector:",
    "moisture:", "software update:", "camera damage:", "previous repair:", "water impact:"
]
SPANISH_LEAK_WORDS_FOR_ENGLISH = ["puede ser", "prueba", "no fuerces", "cargador", "batería", "pantalla", "móvil", "técnico", "humedad"]
LANGUAGE_LEAK_WORDS = {
    "English": SPANISH_LEAK_WORDS_FOR_ENGLISH,
    "Catalan": ["Probable diagnosis:", "What to do now:", "When to visit", "puede ser", "Prueba otro"],
    "Urdu": ["Probable diagnosis:", "What to do now:", "Diagnóstico probable:", "puede ser"],
    "Arabic": ["Probable diagnosis:", "What to do now:", "Diagnóstico probable:", "puede ser"],
    "Romanian": ["Probable diagnosis:", "What to do now:", "Diagnóstico probable:", "puede ser"],
}

def looks_bad_output(answer: str) -> bool:
    if not answer or len(answer.strip()) < 50:
        return True
    a = answer.lower()
    if any(marker in a for marker in INTERNAL_LEAK_MARKERS):
        return True
    numbered = re.findall(r"(?m)^\s*\d+\.", answer)
    if len(numbered) != 5:
        return True
    if re.search(r"(?m)^\s*(?:6|7|8|9|[1-9][0-9])\.\s+", answer):
        return True
    return False

def violates_requested_language(answer: str, language: str) -> bool:
    lang = normalize_language_name(language)
    a = answer or ""
    for marker in LANGUAGE_LEAK_WORDS.get(lang, []):
        if marker.lower() in a.lower():
            return True
    return False

def answer_conflicts_with_category(answer: str, category: str, user_text: str) -> bool:
    a = norm_text(answer)
    if category in {"sim_network_issue", "network_issue"} and not contains_any(user_text, DANGER_WATER_TERMS):
        if any(w in a for w in ["water damage", "liquid", "corrosion", "aigua", "agua", "humedad", "corrosio"]):
            return True
    if category == "app_issue" and any(w in a for w in ["motherboard", "placa", "bootloop", "swollen battery"]):
        return True
    return False


# ============================================================
# Gemma 4 native-style function calling route
# ============================================================

USE_GEMMA_FUNCTION_CALLING = True

def repairwise_decide_escalation(
    escalation_level: str,
    needs_human_technician: bool,
    reason: str,
    customer_safe_next_step: str,
) -> dict:
    """Tool executed after Gemma decides escalation.

    This is intentionally simple and safe: Gemma suggests the routing, but
    RepairWise still keeps deterministic safety triage authoritative.
    """
    allowed = {"self_check", "soon", "urgent"}
    if escalation_level not in allowed:
        escalation_level = "soon" if needs_human_technician else "self_check"
    return {
        "escalation_level": escalation_level,
        "needs_human_technician": bool(needs_human_technician),
        "reason": str(reason)[:220],
        "customer_safe_next_step": str(customer_safe_next_step)[:220],
    }

GEMMA_NATIVE_TOOL_SCHEMAS = [
    {
        "name": "repairwise_decide_escalation",
        "description": "Decide whether the user needs urgent professional help or can self-resolve. Call this for any repair or safety question.",
        "parameters": {
            "type": "object",
            "properties": {
                "escalation_level": {
                    "type": "string",
                    "enum": ["self_resolve", "monitor", "urgent", "emergency"],
                    "description": "Level: self_resolve=user can fix, monitor=watch it, urgent=see tech soon, emergency=stop using now"
                },
                "needs_human_technician": {"type": "boolean", "description": "True if professional repair needed"},
                "reason": {"type": "string", "description": "Brief reason for escalation decision"},
                "customer_safe_next_step": {"type": "string", "description": "Single clearest action the customer should take right now"},
            },
            "required": ["escalation_level", "needs_human_technician", "reason", "customer_safe_next_step"]
        }
    },
    {
        "name": "assess_damage_severity",
        "description": "Score the physical severity of phone damage from 1-10. Call this when user describes physical damage (screen, battery, water, drop).",
        "parameters": {
            "type": "object",
            "properties": {
                "severity_score": {
                    "type": "integer",
                    "description": "Damage severity 1-10: 1-3=cosmetic, 4-6=functional impact, 7-9=serious, 10=dangerous/unusable"
                },
                "damage_type": {
                    "type": "string",
                    "enum": ["screen", "battery", "water", "charging", "software", "audio", "camera", "unknown"],
                    "description": "Primary type of damage"
                },
                "data_at_risk": {"type": "boolean", "description": "True if user data may be at risk"},
                "repair_urgency": {
                    "type": "string",
                    "enum": ["within_24h", "within_week", "when_convenient", "monitor_only"],
                    "description": "How urgently repair is needed"
                },
                "estimated_repair_complexity": {
                    "type": "string",
                    "enum": ["DIY_safe", "professional_basic", "professional_advanced", "board_level"],
                    "description": "Complexity of repair needed"
                }
            },
            "required": ["severity_score", "damage_type", "data_at_risk", "repair_urgency", "estimated_repair_complexity"]
        }
    },
    {
        "name": "check_warranty_status",
        "description": "Check warranty eligibility based on country and estimated purchase date. Call when user asks about warranty, returns, or refunds.",
        "parameters": {
            "type": "object",
            "properties": {
                "likely_covered": {"type": "boolean", "description": "True if device is likely still under warranty"},
                "warranty_years": {
                    "type": "integer",
                    "description": "Legal warranty years in the user country (EU=2, UK=2, US=1, varies)"
                },
                "action_required": {
                    "type": "string",
                    "description": "What the user should do to claim warranty (e.g. contact manufacturer, go to store)"
                },
                "warning": {
                    "type": "string",
                    "description": "Any warranty-voiding risk the user should know about (e.g. water damage, unauthorized repair)"
                }
            },
            "required": ["likely_covered", "warranty_years", "action_required"]
        }
    },
    {
        "name": "detect_scam_signals",
        "description": "Analyse a suspicious SMS or message for phishing/scam indicators. Call this for any message the user thinks might be a scam.",
        "parameters": {
            "type": "object",
            "properties": {
                "scam_probability": {
                    "type": "integer",
                    "description": "Probability this is a scam 0-100%"
                },
                "signals_found": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of scam signals detected (e.g. suspicious_url, urgency_language, data_request, impersonation)"
                },
                "impersonated_entity": {
                    "type": "string",
                    "description": "Who the scammer is pretending to be (e.g. BBVA, Santander, PayPal, Amazon)"
                },
                "safe_action": {
                    "type": "string",
                    "description": "Exact safe action: what the user should do right now"
                }
            },
            "required": ["scam_probability", "signals_found", "safe_action"]
        }
    },
]


def deterministic_escalation_args(user_text: str, triage: dict) -> dict:
    """Deterministic fallback args if Gemma/tool parsing is unavailable."""
    category = triage.get("category", "unknown")
    urgency = triage.get("urgency", "LOW")

    if urgency == "HIGH":
        level = "urgent"
        needs_tech = True
    elif urgency == "MEDIUM":
        level = "soon"
        needs_tech = True
    else:
        level = "self_check"
        needs_tech = False

    category_reason = {
        "battery_safety": "Possible swollen or unsafe battery.",
        "water_damage": "Liquid damage can worsen if the phone is charged.",
        "scam_phishing": "Message may be phishing or credential theft.",
        "charging_issue": "Charging faults can be cable, charger, port, battery, or software.",
        "sim_network_issue": "Coverage issues are usually SIM, carrier settings, APN, software, or antenna related.",
        "app_issue": "App failures are often cache, storage, update, internet, or service outage related.",
    }.get(category, "RepairWise triage found a phone issue that needs safe checks.")

    next_step = {
        "battery_safety": "Stop using and charging the phone.",
        "water_damage": "Turn it off and do not charge it.",
        "scam_phishing": "Do not open links or enter codes/card details.",
        "charging_issue": "Try another certified cable and charger without forcing the port.",
        "sim_network_issue": "Restart, toggle airplane mode and test SIM/network settings.",
        "app_issue": "Restart, update the app, check internet and free storage.",
    }.get(category, "Start with a forced restart and describe the exact symptom.")

    return {
        "escalation_level": level,
        "needs_human_technician": needs_tech,
        "reason": category_reason,
        "customer_safe_next_step": next_step,
    }

def _extract_json_object(text: str):
    if not text:
        return None
    # Try direct JSON first.
    try:
        return json.loads(text)
    except Exception:
        pass
    # Try fenced/tool-call-ish JSON.
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None

def parse_tool_call_args(raw: str) -> dict | None:
    """Parse Gemma tool output from either native tool format or JSON fallback."""
    obj = _extract_json_object(raw)
    if not isinstance(obj, dict):
        return None

    # Common native-ish structures:
    # {"name": "...", "arguments": {...}}
    # {"tool_calls": [{"function": {"name": "...", "arguments": {...}}}]}
    if "tool_calls" in obj and isinstance(obj["tool_calls"], list) and obj["tool_calls"]:
        tc = obj["tool_calls"][0]
        fn = tc.get("function", tc) if isinstance(tc, dict) else {}
        args = fn.get("arguments", {}) if isinstance(fn, dict) else {}
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        return args if isinstance(args, dict) else None

    # Any named tool call
    if obj.get("name") in TOOL_DISPATCH:
        args = obj.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        return args if isinstance(args, dict) else None

    # JSON-only fallback: object is directly the arguments for any tool.
    # Check each tool's required fields
    for tool_required in [
        {"escalation_level", "needs_human_technician", "reason", "customer_safe_next_step"},
        {"severity_score", "damage_type", "data_at_risk", "repair_urgency"},
        {"likely_covered", "warranty_years", "action_required"},
        {"scam_probability", "signals_found", "safe_action"},
    ]:
        if tool_required <= set(obj.keys()):
            return obj

    return None

def build_tool_router_prompt(user_text: str, triage: dict, docs: list, language: str) -> str:
    """Build prompt for Gemma 4 function calling — selects appropriate tool."""
    context = "\n".join(f"[{d.get('id')}] {d.get('text','')[:180]}" for d in docs[:3])
    lang = normalize_language_name(language)
    category = triage.get("category", "unknown")
    urgency = triage.get("urgency", "LOW")

    # Select the most relevant tool for this query
    selected_tool = select_tool_for_category(category, user_text)

    tool_schemas = {
        "repairwise_decide_escalation": '''{{
  "escalation_level": "self_resolve"|"monitor"|"urgent"|"emergency",
  "needs_human_technician": true|false,
  "reason": "brief reason",
  "customer_safe_next_step": "single clear action for customer"
}}''',
        "assess_damage_severity": '''{{
  "severity_score": 1-10,
  "damage_type": "screen"|"battery"|"water"|"charging"|"software"|"audio"|"camera"|"unknown",
  "data_at_risk": true|false,
  "repair_urgency": "within_24h"|"within_week"|"when_convenient"|"monitor_only",
  "estimated_repair_complexity": "DIY_safe"|"professional_basic"|"professional_advanced"|"board_level"
}}''',
        "check_warranty_status": '''{{
  "likely_covered": true|false,
  "warranty_years": 1|2,
  "action_required": "what to do to claim warranty",
  "warning": "any warranty-voiding risk or empty string"
}}''',
        "detect_scam_signals": '''{{
  "scam_probability": 0-100,
  "signals_found": ["suspicious_url","urgency_language","data_request","impersonation","grammar_errors","unusual_sender"],
  "impersonated_entity": "bank name or service",
  "safe_action": "exact action user should take"
}}''',
    }

    schema = tool_schemas.get(selected_tool, tool_schemas["repairwise_decide_escalation"])

    return f"""You are RepairWise AI assistant. Analyse the customer message and call the appropriate tool.

Customer message: {user_text}
Category: {category} | Urgency: {urgency}
Context: {context[:400]}

Call tool: {selected_tool}
Return ONLY the JSON arguments for {selected_tool}:
{schema}

Do not write anything else. Only the JSON object.""".strip()


# ── Tool implementations ──────────────────────────────────────────────────────

def assess_damage_severity(severity_score: int, damage_type: str,
                           data_at_risk: bool, repair_urgency: str,
                           estimated_repair_complexity: str, **kwargs) -> dict:
    """Tool: score physical damage severity 1-10."""
    score = max(1, min(10, int(severity_score)))
    urgency_map = {
        "within_24h": "🔴 See a technician within 24 hours",
        "within_week": "🟡 Book a repair within the week",
        "when_convenient": "🟢 Repair when convenient",
        "monitor_only": "🟢 Monitor — no immediate repair needed",
    }
    complexity_map = {
        "DIY_safe": "Can be attempted at home with care",
        "professional_basic": "Standard repair shop — 30-60 min",
        "professional_advanced": "Specialist repair required",
        "board_level": "Board-level repair — complex and expensive",
    }
    return {
        "severity_score": score,
        "severity_label": (
            "🔴 Critical" if score >= 8 else
            "🟡 Serious" if score >= 5 else
            "🟢 Minor"
        ),
        "damage_type": damage_type,
        "data_at_risk": bool(data_at_risk),
        "repair_urgency": urgency_map.get(repair_urgency, repair_urgency),
        "repair_complexity": complexity_map.get(estimated_repair_complexity, estimated_repair_complexity),
        "data_backup_recommended": bool(data_at_risk) or score >= 6,
    }

def check_warranty_status(likely_covered: bool, warranty_years: int,
                          action_required: str, warning: str = "", **kwargs) -> dict:
    """Tool: check warranty eligibility."""
    return {
        "likely_covered": bool(likely_covered),
        "warranty_years": int(warranty_years),
        "status": "✅ Likely under warranty" if likely_covered else "⚠️ Warranty may have expired",
        "action_required": str(action_required),
        "warning": str(warning) if warning else None,
        "tip": (
            "Keep your purchase receipt. Avoid unauthorized repairs — they void the warranty."
            if likely_covered else
            "Even outside warranty, manufacturer goodwill repairs are sometimes possible."
        ),
    }

def detect_scam_signals(scam_probability: int, signals_found: list,
                        safe_action: str, impersonated_entity: str = "", **kwargs) -> dict:
    """Tool: analyse phishing/scam signals in a message."""
    prob = max(0, min(100, int(scam_probability)))
    signal_labels = {
        "suspicious_url": "⚠️ Suspicious URL",
        "urgency_language": "⚠️ Urgency pressure",
        "data_request": "🔴 Requests sensitive data",
        "impersonation": "🔴 Impersonates trusted entity",
        "grammar_errors": "⚠️ Grammar/spelling errors",
        "unusual_sender": "⚠️ Unusual sender number",
        "too_good_to_be_true": "⚠️ Too-good-to-be-true offer",
        "threatening_language": "🔴 Threatening language",
    }
    return {
        "scam_probability": prob,
        "verdict": (
            "🔴 VERY LIKELY SCAM" if prob >= 80 else
            "🟡 SUSPICIOUS" if prob >= 50 else
            "🟢 PROBABLY LEGITIMATE"
        ),
        "signals_detected": [signal_labels.get(s, s) for s in (signals_found or [])],
        "signal_count": len(signals_found or []),
        "impersonated_entity": str(impersonated_entity) if impersonated_entity else "Unknown",
        "safe_action": str(safe_action),
        "never_do": "Never click links in SMS. Never share PIN, OTP, or card numbers via message.",
    }

# ── Smart tool selector ───────────────────────────────────────────────────────
def select_tool_for_category(category: str, user_text: str) -> str:
    """Select the most appropriate tool based on triage category."""
    text = user_text.lower()
    if category in {"scam_phishing"} or any(
        x in text for x in ["sms", "banco", "bank", "phishing", "link", "enlace"]
    ):
        return "detect_scam_signals"
    if category in {"screen_repair", "battery_safety", "water_damage",
                    "charging_issue", "overheating_issue"}:
        return "assess_damage_severity"
    if any(x in text for x in ["garantia", "garantía", "warranty", "devolver",
                                "refund", "return", "compra"]):
        return "check_warranty_status"
    return "repairwise_decide_escalation"

# ── Unified tool dispatcher ───────────────────────────────────────────────────
TOOL_DISPATCH = {
    "repairwise_decide_escalation": repairwise_decide_escalation,
    "assess_damage_severity": assess_damage_severity,
    "check_warranty_status": check_warranty_status,
    "detect_scam_signals": detect_scam_signals,
}

def dispatch_tool(tool_name: str, args: dict) -> dict:
    """Call the appropriate tool function by name."""
    fn = TOOL_DISPATCH.get(tool_name)
    if fn is None:
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return fn(**args)
    except Exception as e:
        return {"error": f"{tool_name} failed: {e}"}


def deterministic_scam_args(user_text: str, triage: dict) -> dict:
    """Deterministic fallback args for detect_scam_signals."""
    t = user_text.lower()
    signals = []
    if any(x in t for x in ["http", "bit.ly", "tinyurl", ".xyz", "link", "enlace", "url"]):
        signals.append("suspicious_url")
    if any(x in t for x in ["urgente", "urgent", "ahora", "immediately", "suspended",
                              "bloqueada", "suspendida", "immediately"]):
        signals.append("urgency_language")
    if any(x in t for x in ["tarjeta", "card", "pin", "contraseña", "password",
                              "otp", "codigo", "clave", "cuenta", "account"]):
        signals.append("data_request")
    if any(x in t for x in ["bbva", "santander", "caixabank", "sabadell", "bankia",
                              "ing", "paypal", "amazon", "correos", "hacienda", "banco", "bank"]):
        signals.append("impersonation")
    
    entity = "Unknown"
    for bank in ["bbva", "santander", "caixabank", "sabadell", "bankia", "ing",
                 "paypal", "amazon", "correos"]:
        if bank in t:
            entity = bank.upper()
            break

    prob = min(99, len(signals) * 22 + (15 if len(signals) > 0 else 0))
    return {
        "scam_probability": prob,
        "signals_found": signals if signals else ["suspicious_message"],
        "impersonated_entity": entity,
        "safe_action": "Do not click links or enter codes/card details. Contact your bank directly.",
    }


def deterministic_damage_args(user_text: str, triage: dict) -> dict:
    """Deterministic fallback args for assess_damage_severity."""
    cat = triage.get("category", "unknown")
    urgency = triage.get("urgency", "LOW")
    
    severity_map = {
        "battery_safety": 9, "water_damage": 8, "overheating_issue": 7,
        "screen_repair": 5, "charging_issue": 4, "charging_port_issue": 4,
    }
    damage_type_map = {
        "battery_safety": "battery", "water_damage": "water",
        "screen_repair": "screen", "charging_issue": "charging",
        "overheating_issue": "battery", "charging_port_issue": "charging",
    }
    return {
        "severity_score": severity_map.get(cat, 5),
        "damage_type": damage_type_map.get(cat, "unknown"),
        "data_at_risk": urgency in {"HIGH", "MEDIUM"},
        "repair_urgency": "within_24h" if urgency == "HIGH" else (
            "within_week" if urgency == "MEDIUM" else "when_convenient"),
        "estimated_repair_complexity": "professional_basic",
    }


def deterministic_warranty_args(user_text: str, triage: dict) -> dict:
    """Deterministic fallback args for check_warranty_status."""
    t = user_text.lower()
    # Spain: 2 years legal warranty
    likely = not any(x in t for x in ["agua", "water", "caído", "dropped",
                                        "roto", "broken", "accidente", "accident"])
    return {
        "likely_covered": likely,
        "warranty_years": 2,
        "action_required": "Contact the manufacturer or original retailer with your proof of purchase.",
        "warning": "Water damage or physical impact may void the warranty." if not likely else "",
    }


def deterministic_args_for_tool(tool_name: str, user_text: str, triage: dict) -> dict:
    """Route to the correct deterministic fallback for each tool."""
    if tool_name == "detect_scam_signals":
        return deterministic_scam_args(user_text, triage)
    elif tool_name == "assess_damage_severity":
        return deterministic_damage_args(user_text, triage)
    elif tool_name == "check_warranty_status":
        return deterministic_warranty_args(user_text, triage)
    else:
        return deterministic_escalation_args(user_text, triage)

def call_gemma_function_router(user_text: str, triage: dict, docs: list, language: str) -> dict:
    """Try Gemma 4 native function calling, with JSON fallback.

    If the local tokenizer supports `apply_chat_template(..., tools=...)`, we pass
    the tool schema directly. If not, we fall back to a JSON tool-call prompt.
    """
    trace = LAST_GEMMA_TRACE["function_calling"]
    trace.update({
        "attempted": True,
        "native_tools_passed": False,
        "tool_name": selected_tool_name if "selected_tool_name" in dir() else "repairwise_decide_escalation",
        "tool_args": {},
        "tool_result": {},
        "raw": "",
        "error": "",
    })

    # Select the best tool for this query category
    selected_tool_name = select_tool_for_category(triage.get("category",""), user_text)
    trace["tool_name"] = selected_tool_name

    if not USE_GEMMA_FUNCTION_CALLING:
        args = deterministic_args_for_tool(selected_tool_name, user_text, triage)
        result = dispatch_tool(selected_tool_name, args)
        trace.update({"tool_args": args, "tool_result": result, "error": "Function calling disabled."})
        return result

    if not ("processor" in globals() and "model" in globals()):
        args = deterministic_args_for_tool(selected_tool_name, user_text, triage)
        result = dispatch_tool(selected_tool_name, args)
        LAST_GEMMA_TRACE.update({
            "called": True, "path": "function_calling_unavailable",
            "fallback_used": True, "error": "Gemma model not loaded in this runtime.",
        })
        trace.update({"tool_args": args, "tool_result": result, "error": "Gemma model not loaded in this runtime."})
        return result

    prompt = build_tool_router_prompt(user_text, triage, docs, language)

    try:
        tokenizer = getattr(processor, "tokenizer", processor)
        native_prompt = None

        # Native function-calling path when the tokenizer supports tool schemas.
        if hasattr(tokenizer, "apply_chat_template"):
            messages = [{"role": "user", "content": prompt}]
            try:
                native_prompt = tokenizer.apply_chat_template(
                    messages,
                    tools=GEMMA_NATIVE_TOOL_SCHEMAS,
                    tokenize=False,
                    add_generation_prompt=True,
                )
                trace["native_tools_passed"] = True
            except TypeError:
                native_prompt = None
            except Exception as e:
                trace["error"] = f"native tools path failed, using JSON fallback: {type(e).__name__}: {e}"
                native_prompt = None

        final_prompt = native_prompt or prompt
        inputs = processor(text=final_prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=160,
                do_sample=False,
                temperature=None,
                top_p=None,
                repetition_penalty=1.08,
                eos_token_id=processor.tokenizer.eos_token_id,
                pad_token_id=processor.tokenizer.eos_token_id,
            )

        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
        raw = processor.decode(generated_ids, skip_special_tokens=True).replace("<end_of_turn>", "").strip()
        trace["raw"] = raw[:1200]
        LAST_GEMMA_TRACE.update({"called": True, "path": "function_calling_router", "raw": raw[:1200]})

        args = parse_tool_call_args(raw) or deterministic_escalation_args(user_text, triage)
        # Ensure all required keys exist and execute the tool.
        defaults = deterministic_escalation_args(user_text, triage)
        defaults.update({k: v for k, v in args.items() if v is not None})
        result = dispatch_tool(selected_tool_name, defaults)
        trace.update({"tool_args": defaults, "tool_result": result})
        return result

    except Exception as exc:
        args = deterministic_args_for_tool(selected_tool_name, user_text, triage)
        result = dispatch_tool(selected_tool_name, args)
        err = f"{type(exc).__name__}: {exc}"
        LAST_GEMMA_TRACE.update({"called": True, "path": "function_calling_error", "fallback_used": True, "error": err})
        trace.update({"tool_name": selected_tool_name, "tool_args": args, "tool_result": result, "error": err})
        return result



# ============================================================
# Real Transformers streaming with TextIteratorStreamer
# ============================================================

def gemma_model_available() -> bool:
    return "processor" in globals() and "model" in globals()

def stream_gemma_generate(
    prompt: str,
    image=None,
    max_new_tokens: int = 220,
    repetition_penalty: float = 1.12,
    path: str = "text_iterator_streamer",
):
    """Yield real Gemma tokens/chunks from transformers.TextIteratorStreamer.

    This is not simulated word-by-word streaming. A generation thread calls
    model.generate(..., streamer=streamer), and Gradio receives chunks as the
    model produces them.
    """
    LAST_GEMMA_TRACE["streaming"].update({
        "enabled": True,
        "mode": "TextIteratorStreamer",
        "chunks": 0,
        "raw": "",
        "error": "",
    })
    LAST_GEMMA_TRACE.update({"called": True, "path": path, "raw": "", "fallback_used": False, "error": ""})

    if not gemma_model_available():
        err = "Gemma model not loaded in this runtime."
        LAST_GEMMA_TRACE["streaming"]["error"] = err
        LAST_GEMMA_TRACE["error"] = err
        LAST_GEMMA_TRACE["fallback_used"] = True
        return

    try:
        if image is not None:
            inputs = processor(text=prompt, images=image, return_tensors="pt")
        else:
            inputs = processor(text=prompt, return_tensors="pt")

        inputs = {k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}
        tokenizer = getattr(processor, "tokenizer", processor)
        streamer = TextIteratorStreamer(
            tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
            timeout=120,
        )

        generation_kwargs = dict(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            repetition_penalty=repetition_penalty,
            eos_token_id=processor.tokenizer.eos_token_id,
            pad_token_id=processor.tokenizer.eos_token_id,
            streamer=streamer,
        )

        thread = threading.Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()

        raw_parts = []
        for chunk in streamer:
            if chunk:
                raw_parts.append(chunk)
                LAST_GEMMA_TRACE["streaming"]["chunks"] += 1
                current = "".join(raw_parts)
                LAST_GEMMA_TRACE["streaming"]["raw"] = current[:1600]
                LAST_GEMMA_TRACE["raw"] = current[:1600]
                yield chunk

        thread.join(timeout=5)

    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
        LAST_GEMMA_TRACE["streaming"]["error"] = err
        LAST_GEMMA_TRACE["error"] = err
        LAST_GEMMA_TRACE["fallback_used"] = True
        return

def clean_streamed_answer(raw: str) -> str:
    text = (raw or "").replace("<end_of_turn>", "").replace("<start_of_turn>", "").strip()
    text = re.sub(r"^[?!.,;:\s]+", "", text)
    return text


def build_text_enrichment_prompt(base_answer: str, user_text: str, triage: dict, docs: list, language: str) -> str:
    lang = normalize_language_name(language)
    label_instruction = LANGUAGE_INSTRUCTIONS.get(lang, LANGUAGE_INSTRUCTIONS["Spanish"])
    context = "\n".join(f"[{d.get('id')}] {d.get('text','')[:350]}" for d in docs[:3])
    return f"""
You are RepairWise AI, an offline assistant for a real mobile phone repair shop.
{label_instruction}

Your job is NOT to invent a new diagnosis. Improve the wording of the base answer using only the local context.
Keep the same risk level and the same 5-line numbered format.
Do not add prices. Do not mention motherboard/board/internal damage unless the context explicitly says it.
Return exactly 5 numbered lines.

Customer message:
{user_text}

Detected category:
{triage.get('category')}

Local context:
{context}

Base answer to preserve:
{base_answer}
""".strip()

def call_gemma_text(prompt: str, max_new_tokens: int = 220) -> str:
    LAST_GEMMA_TRACE.update({"called": True, "path": "text_enrichment", "raw": "", "fallback_used": False, "error": "",
                              "backend": "ollama" if _USE_OLLAMA else "transformers"})
    # ── Ollama backend (Cactus-aware: routes E2B vs E4B) ─────────────────────
    if _USE_OLLAMA:
        try:
            cactus_tier = LAST_ROUTER_DECISION.get("selected_tier", "e2b")
            if cactus_tier == "e4b":
                # High-complexity query → route to E4B model
                raw = _call_e4b_via_ollama(prompt, max_tokens=max_new_tokens)
                LAST_GEMMA_TRACE["path"] = "cactus_ollama_e4b"
            else:
                raw = _ollama_chat(prompt, max_tokens=max_new_tokens)
                LAST_GEMMA_TRACE["path"] = "cactus_ollama_e2b"
            LAST_GEMMA_TRACE["raw"] = raw[:1200]
            LAST_GEMMA_TRACE["cactus_model"] = LAST_ROUTER_DECISION.get("actual_model_called", OLLAMA_MODEL)
            return raw
        except Exception as exc:
            LAST_GEMMA_TRACE["error"] = f"Ollama: {exc}"
    # ── llama.cpp backend ─────────────────────────────────────────────────────
    if _USE_LLAMACPP:
        try:
            raw = _llamacpp_chat(prompt, max_tokens=max_new_tokens)
            LAST_GEMMA_TRACE["raw"] = raw[:1200]
            LAST_GEMMA_TRACE["path"] = "llamacpp_text_enrichment"
            LAST_GEMMA_TRACE["backend"] = "llamacpp"
            return raw
        except Exception as exc:
            LAST_GEMMA_TRACE["error"] = f"llama.cpp: {exc}"
    # ── Transformers backend ──────────────────────────────────────────────────
    try:
        inputs = processor(text=prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                repetition_penalty=1.12,
                eos_token_id=processor.tokenizer.eos_token_id,
                pad_token_id=processor.tokenizer.eos_token_id,
            )
        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
        raw = processor.decode(generated_ids, skip_special_tokens=True).replace("<end_of_turn>", "").strip()
        LAST_GEMMA_TRACE["raw"] = raw[:1200]
        return raw
    except Exception as exc:
        LAST_GEMMA_TRACE["error"] = f"{type(exc).__name__}: {exc}"
        LAST_GEMMA_TRACE["fallback_used"] = True
        return ""


USE_GEMMA_HIGH_RISK_CONTEXT = True

CONTEXT_NOTE_LABELS = {
    "Spanish": "Nota específica",
    "English": "Specific note",
    "Catalan": "Nota específica",
    "Urdu": "خاص نوٹ",
    "Arabic": "ملاحظة خاصة",
    "Romanian": "Notă specifică",
}


TOOL_NEXT_STEP_LABELS = {
    "Spanish": "Paso decidido por la herramienta",
    "English": "Tool-selected next step",
    "Catalan": "Pas decidit per l'eina",
    "Urdu": "ٹول کا منتخب اگلا قدم",
    "Arabic": "الخطوة التي اختارتها الأداة",
    "Romanian": "Pas ales de instrument",
}

TOOL_STEP_TRANSLATIONS = {
    "Start with a forced restart and describe the exact symptom.": {
        "Spanish": "Haz un reinicio forzado y describe el síntoma exacto.",
        "Catalan": "Fes un reinici forçat i descriu el símptoma exacte.",
        "Arabic": "أعد تشغيل الهاتف قسراً وصف العَرَض بدقة.",
        "Romanian": "Fă un restart forțat și descrie simptomul exact.",
        "Urdu": "فورسڈ ری اسٹارٹ کریں اور علامت بیان کریں۔",
    },
    "Do not open links or enter codes/card details.": {
        "Spanish": "No abras enlaces ni introduzcas códigos ni datos de tarjeta.",
        "Catalan": "No obris enllaços ni introdueixis codis ni dades de targeta.",
        "Arabic": "لا تفتح الروابط ولا تدخل الرموز أو بيانات البطاقة.",
        "Romanian": "Nu deschide linkuri și nu introduce coduri sau date de card.",
        "Urdu": "لنک نہ کھولیں اور کوڈ یا کارڈ کی تفصیل نہ دیں۔",
    },
    "Stop charging immediately and let the phone cool down.": {
        "Spanish": "Deja de cargarlo y deja que el teléfono se enfríe.",
        "Catalan": "Deixa de carregar-lo i deixa que el telèfon es refredi.",
        "Arabic": "أوقف الشحن فوراً واترك الهاتف يبرد.",
        "Romanian": "Oprește încărcarea imediat și lasă telefonul să se răcească.",
        "Urdu": "فوری چارجنگ بند کریں اور فون ٹھنڈا ہونے دیں۔",
    },
}

def translate_tool_step(step: str, language: str) -> str:
    """Translate common English tool steps to the response language."""
    translations = TOOL_STEP_TRANSLATIONS.get(step, {})
    return translations.get(language, step)

def inject_tool_next_step(answer: str, tool_result: dict | None, language: str) -> str:
    """Connect function-calling output to the visible customer answer."""
    if not answer or not tool_result:
        return answer
    step = str(tool_result.get("customer_safe_next_step", "")).strip()
    if not step or step.lower() in answer.lower():
        return answer

    lang = normalize_language_name(language)
    # Translate the tool step to the response language
    step_translated = translate_tool_step(step, lang)
    label = TOOL_NEXT_STEP_LABELS.get(lang, "Tool-selected next step")
    answer_lines = answer.splitlines()

    # Put the tool step in line 3 ("What to do now")
    if len(answer_lines) >= 3:
        answer_lines[2] = answer_lines[2].rstrip() + f" {label}: {step_translated}"
        return "\n".join(answer_lines)

    return answer + f"\n{label}: {step_translated}"


def build_high_risk_context_prompt(base_answer: str, user_text: str, triage: dict, docs: list, language: str) -> str:
    """Ask Gemma 4 for one short contextual sentence for HIGH-risk cases.

    Important: this sentence is used only as an add-on to the safe template.
    It never replaces the deterministic safety answer.
    """
    lang = normalize_language_name(language)
    label_instruction = LANGUAGE_INSTRUCTIONS.get(lang, LANGUAGE_INSTRUCTIONS["Spanish"])
    context = "\n".join(f"[{d.get('id')}] {d.get('text','')[:280]}" for d in docs[:3])
    return f"""
You are RepairWise AI, an offline mobile repair assistant.
{label_instruction}

The base answer below is safety-critical. Do NOT replace it.
Write ONE short contextual sentence, max 22 words, personalized to the customer message.
Do not add prices. Do not add a new diagnosis. Do not reduce the risk level.
Do not mention motherboard, IC, board-level damage, or internal damage unless the context explicitly says it.
Return only the sentence, no numbering, no bullets.

Customer message:
{user_text}

Detected category:
{triage.get('category')}

Local context:
{context}

Safety base answer:
{base_answer}
""".strip()

def call_gemma_high_risk_context(prompt: str, max_new_tokens: int = 64) -> str:
    LAST_GEMMA_TRACE.update({"called": True, "path": "high_risk_context", "raw": "", "fallback_used": False, "error": ""})
    try:
        inputs = processor(text=prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                repetition_penalty=1.18,
                eos_token_id=processor.tokenizer.eos_token_id,
                pad_token_id=processor.tokenizer.eos_token_id,
            )
        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
        raw = processor.decode(generated_ids, skip_special_tokens=True).replace("<end_of_turn>", "").strip()
        raw = re.sub(r"^\s*[-*•\d.)]+\s*", "", raw)
        raw = re.sub(r"\s+", " ", raw).strip()
        LAST_GEMMA_TRACE["raw"] = raw[:1200]
        return raw
    except Exception as exc:
        LAST_GEMMA_TRACE["error"] = f"{type(exc).__name__}: {exc}"
        LAST_GEMMA_TRACE["fallback_used"] = True
        return ""

def clean_context_sentence(raw: str, language: str, category: str, user_text: str) -> str:
    """Validate a one-sentence Gemma context note before inserting into the template."""
    if not raw:
        return ""
    text = raw.strip().replace("\n", " ")
    text = re.sub(r"^\s*(1\.|2\.|3\.|4\.|5\.)\s*", "", text).strip()
    # Keep only first sentence-ish chunk to avoid format drift.
    parts = re.split(r"(?<=[.!?۔؟])\s+", text)
    text = parts[0].strip() if parts else text
    if len(text) < 12 or len(text) > 220:
        return ""
    if looks_bad_output(text):
        return ""
    if violates_requested_language(text, language):
        return ""
    if answer_conflicts_with_category(text, category, user_text):
        return ""
    banned = [
        "replace motherboard", "motherboard is damaged", "board is damaged",
        "ic is damaged", "placa está dañada", "cambiar la placa",
        "guaranteed", "100%", "definitely"
    ]
    if any(b in text.lower() for b in banned):
        return ""
    return text

def inject_context_note(base_answer: str, note: str, language: str) -> str:
    """Insert the Gemma 4 note into line 1 while preserving exactly 5 numbered lines."""
    if not note:
        return base_answer
    lang = normalize_language_name(language)
    label = CONTEXT_NOTE_LABELS.get(lang, "Specific note")
    lines = base_answer.splitlines()
    if not lines:
        return base_answer
    lines[0] = lines[0].rstrip() + f" {label}: {note}"
    return "\n".join(lines)


def generate_text_answer(user_text: str, triage: dict, docs: list, language: str) -> str:
    lang = normalize_language_name(language)
    category = triage.get("category", "unknown")
    urgency = triage.get("urgency", "LOW")
    base = safe_fallback_answer(user_text, triage, docs, lang, image_present=False)

    # Route 0: Gemma 4 function calling / tool routing.
    # This demonstrates native/tool-use behavior without allowing the model to override safety.
    if len(norm_text(user_text).split()) >= 3:
        tool_result = call_gemma_function_router(user_text, triage, docs, lang)
    else:
        _sel = select_tool_for_category(triage.get("category",""), user_text)
        tool_result = dispatch_tool(_sel, deterministic_escalation_args(user_text, triage))
        LAST_GEMMA_TRACE["function_calling"].update({
            "attempted": False,
            "tool_name": selected_tool_name if "selected_tool_name" in dir() else "repairwise_decide_escalation",
            "tool_args": deterministic_escalation_args(user_text, triage),
            "tool_result": tool_result,
        })

    base = inject_tool_next_step(base, tool_result, lang)

    # Route A: LOW/MEDIUM text enrichment can replace the base answer only if it passes all guards.
    if (
        USE_GEMMA_TEXT_ENRICHMENT
        and category in TEXT_GEMMA_ENRICH_CATEGORIES
        and urgency != "HIGH"
        and "processor" in globals()
        and "model" in globals()
    ):
        prompt = build_text_enrichment_prompt(base, user_text, triage, docs, lang)
        raw = call_gemma_text(prompt)
        # Preserve function-calling trace even after the enrichment call overwrites path/raw.
        LAST_GEMMA_TRACE["function_calling"]["tool_result"] = tool_result
        if raw and not looks_bad_output(raw) and not violates_requested_language(raw, lang) and not answer_conflicts_with_category(raw, category, user_text):
            return inject_tool_next_step(raw[:1800], tool_result, lang)
        LAST_GEMMA_TRACE["fallback_used"] = True

    elif USE_GEMMA_TEXT_ENRICHMENT and category in TEXT_GEMMA_ENRICH_CATEGORIES and urgency != "HIGH":
        LAST_GEMMA_TRACE.update({
            "called": True,
            "path": "text_enrichment_unavailable",
            "raw": "",
            "fallback_used": True,
            "error": "Gemma model not loaded in this runtime."
        })
        LAST_GEMMA_TRACE["function_calling"]["tool_result"] = tool_result

    # Route B: HIGH-risk context note. The safe template remains authoritative.
    if (
        USE_GEMMA_TEXT_ENRICHMENT
        and USE_GEMMA_HIGH_RISK_CONTEXT
        and urgency == "HIGH"
        and category in HIGH_RISK_CATEGORIES
        and "processor" in globals()
        and "model" in globals()
    ):
        prompt = build_high_risk_context_prompt(base, user_text, triage, docs, lang)
        raw = call_gemma_high_risk_context(prompt)
        LAST_GEMMA_TRACE["function_calling"]["tool_result"] = tool_result
        note = clean_context_sentence(raw, lang, category, user_text)
        if note:
            return inject_context_note(base, note, lang)
        LAST_GEMMA_TRACE["fallback_used"] = True

    elif USE_GEMMA_TEXT_ENRICHMENT and USE_GEMMA_HIGH_RISK_CONTEXT and urgency == "HIGH" and category in HIGH_RISK_CATEGORIES:
        LAST_GEMMA_TRACE.update({
            "called": True,
            "path": "high_risk_context_unavailable",
            "raw": "",
            "fallback_used": True,
            "error": "Gemma model not loaded in this runtime."
        })
        LAST_GEMMA_TRACE["function_calling"]["tool_result"] = tool_result

    return base



def describe_image_with_gemma(image, language: str = "English") -> str:
    """Use Gemma 4 to describe visible image evidence before photo triage.

    This makes the photo pipeline genuinely multimodal before final answer
    generation. The description is cautious and used as extra context only.
    """
    lang = normalize_language_name(language)
    LAST_GEMMA_TRACE["image_description"].update({"called": False, "raw": "", "error": ""})

    if image is None:
        return ""
    if not ("processor" in globals() and "model" in globals()):
        LAST_GEMMA_TRACE["image_description"].update({
            "called": True,
            "raw": "",
            "error": "Gemma model not loaded in this runtime."
        })
        return ""

    prompt = (
        "You are helping a phone repair assistant. Describe only what is visibly shown in this phone photo or screenshot "
        "in one cautious sentence. Do not diagnose hidden internal damage. Mention if it looks like a screenshot, cracked screen, "
        "charging port, water/corrosion, swollen battery/lifted screen, camera lens issue, app error, SMS scam, or unclear image."
    )
    try:
        inputs = processor(text=prompt, images=image, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=80,
                do_sample=False,
                temperature=None,
                top_p=None,
                repetition_penalty=1.12,
                eos_token_id=processor.tokenizer.eos_token_id,
                pad_token_id=processor.tokenizer.eos_token_id,
            )
        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
        raw = processor.decode(generated_ids, skip_special_tokens=True).replace("<end_of_turn>", "").strip()
        raw = re.sub(r"\s+", " ", raw)[:300]
        LAST_GEMMA_TRACE["image_description"].update({"called": True, "raw": raw, "error": ""})
        LAST_GEMMA_TRACE["called"] = True
        return raw
    except Exception as exc:
        LAST_GEMMA_TRACE["image_description"].update({
            "called": True,
            "raw": "",
            "error": f"{type(exc).__name__}: {exc}"
        })
        return ""


def image_quality_report(image) -> dict:
    try:
        import numpy as _np
        img = image.convert("RGB")
        w, h = img.size
        small = min(w, h) < 300
        sample = img.resize((min(512, w), max(1, int(h * min(512, w) / max(1, w)))))
        gray = _np.asarray(sample.convert("L"), dtype=_np.float32)
        brightness = float(gray.mean())
        contrast = float(gray.std())
        gx = _np.diff(gray, axis=1) if gray.shape[1] > 2 else _np.array([0])
        gy = _np.diff(gray, axis=0) if gray.shape[0] > 2 else _np.array([0])
        sharpness = float(gx.var() + gy.var())
        issues = []
        if small: issues.append("low_resolution")
        if brightness < 25: issues.append("too_dark")
        if brightness > 235: issues.append("too_bright")
        if contrast < 12: issues.append("low_contrast")
        if sharpness < 18 and contrast >= 12: issues.append("possibly_blurry")
        quality = "poor" if len(issues) >= 2 or (small and issues) else "ok"
        return {"width": int(w), "height": int(h), "brightness": round(brightness, 1), "contrast": round(contrast, 1), "sharpness": round(sharpness, 1), "issues": issues, "quality": quality}
    except Exception as exc:
        return {"quality": "unknown", "issues": [f"quality_check_failed:{type(exc).__name__}"]}

def classify_photo_intent_from_text(text: str) -> dict:
    t = norm_text(text)
    best_key, best_score = "photo_unclear", 0
    for visual_key, info in PHOTO_VISUAL_CATEGORIES.items():
        score = sum(1 for kw in info["keywords"] if norm_text(kw) in t)
        if score > best_score:
            best_key, best_score = visual_key, score
    info = PHOTO_VISUAL_CATEGORIES[best_key]
    return {"visual_category": best_key, "repair_category": info["repair_category"], "risk": info["risk"], "sources": info["sources"], "score": best_score}

def photo_docs_for_category(repair_category: str, visual_category: str | None = None) -> list[dict]:
    wanted = []
    if visual_category in PHOTO_VISUAL_CATEGORIES:
        wanted.extend(PHOTO_VISUAL_CATEGORIES[visual_category]["sources"])
    for key, info in PHOTO_VISUAL_CATEGORIES.items():
        if info["repair_category"] == repair_category:
            wanted.extend(info["sources"])
    docs = []
    for sid in dict.fromkeys(wanted):
        doc = next((dict(d) for d in LOCAL_KNOWLEDGE if d.get("id") == sid), None)
        if doc:
            doc["score"] = 0.92
            doc["engine_scores"] = {"photo_rule": 0.92}
            docs.append(doc)

    # Category relevance boost — matching docs rank higher, off-category penalized
    # Treat scam sub-categories as scam_phishing for RAG purposes
    rag_category = "scam_phishing" if category == "scam_clicked_link" else category
    if rag_category and docs and rag_category not in {"unknown", "vague_problem", "photo_unclear"}:
        matching = []
        others = []
        for _d in docs:
            _d = dict(_d)
            if _d.get("category") == category:
                _d["score"] = float(_d.get("score", 0)) * 2.0
                matching.append(_d)
            else:
                _d["score"] = float(_d.get("score", 0)) * 0.65
                others.append(_d)
        # Sort each group by score
        matching.sort(key=lambda d: float(d.get("score", 0)), reverse=True)
        others.sort(key=lambda d: float(d.get("score", 0)), reverse=True)
        # Matching docs first, then best non-matching to fill slots
        docs = matching + others

    return docs

PHOTO_HIDDEN_DAMAGE_CLAIMS = [
    "motherboard is damaged", "board is damaged", "logic board is damaged", "ic is damaged",
    "must replace the motherboard", "internal water damage is confirmed", "placa está dañada seguro",
    "hay que cambiar la placa", "ic de carga está dañado seguro",
]

def looks_unsafe_photo_answer(answer: str) -> bool:
    a = (answer or "").lower()
    return looks_bad_output(answer) or any(claim in a for claim in PHOTO_HIDDEN_DAMAGE_CLAIMS)

def build_photo_prompt(user_text: str, triage: dict, docs: list, language: str, quality: dict) -> str:
    lang = normalize_language_name(language)
    labels = LABELS.get(lang, LABELS["Spanish"])
    context = "\n".join(f"[{d.get('id')}] {d.get('text','')[:450]}" for d in docs[:4])
    return f"""
You are RepairWise AI, an offline multimodal assistant for a real mobile repair shop.
{LANGUAGE_INSTRUCTIONS.get(lang, LANGUAGE_INSTRUCTIONS['Spanish'])}

Inspect the customer photo/screenshot plus the message. Use only visible evidence.
Do NOT claim hidden motherboard, IC, battery, Face ID, or internal water damage from a photo alone.
If the photo is unclear, dark, blurry, cropped, or too small, say it is not clear enough and ask for a better photo.
If it is an SMS/bank/link/OTP/card screenshot, treat it as possible phishing.
If it is an app error screenshot, give software/app checks first.
If it shows swollen battery/lifted screen/back gap, mark HIGH risk and tell the customer not to charge it.
Never invent prices or guaranteed part replacement.

Detected category: {triage.get('category')}
Risk: {triage.get('urgency')}
Image quality: {quality}

Local context:
{context}

Customer message:
{user_text}

Return EXACTLY 5 numbered lines:
1. {labels[0]}:
2. {labels[1]}:
3. {labels[2]}:
4. {labels[3]}:
5. {labels[4]}:
""".strip()

def call_gemma_photo(prompt: str, image, max_new_tokens: int = 280) -> str:
    LAST_GEMMA_TRACE.update({"called": True, "path": "multimodal_photo", "raw": "", "fallback_used": False, "error": "",
                              "backend": "ollama" if _USE_OLLAMA else "transformers"})
    # ── llama.cpp backend (text+image via base64) ─────────────────────────────
    if _USE_LLAMACPP:
        try:
            import base64 as _b64
            from io import BytesIO as _BytesIO
            buf = _BytesIO()
            image.save(buf, format="JPEG", quality=85)
            img_b64 = _b64.b64encode(buf.getvalue()).decode()
            payload = _json.dumps({
                "prompt": prompt,
                "image_data": [{"data": img_b64, "id": 1}],
                "n_predict": max_new_tokens,
                "temperature": 0.4,
                "repeat_penalty": 1.15,
                "stop": ["<end_of_turn>", "<start_of_turn>"],
                "stream": False,
            }).encode()
            req = _urllib_req.Request(
                f"{LLAMACPP_URL}/completion",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with _urllib_req.urlopen(req, timeout=120) as resp:
                data = _json.loads(resp.read())
                raw = data.get("content", "").replace("<end_of_turn>", "").strip()
                LAST_GEMMA_TRACE["raw"] = raw[:1200]
                LAST_GEMMA_TRACE["path"] = "llamacpp_multimodal_photo"
                LAST_GEMMA_TRACE["backend"] = "llamacpp"
                return raw
        except Exception as exc:
            LAST_GEMMA_TRACE["error"] = f"llama.cpp photo: {exc}"
    # ── Ollama backend (text-only for photo — vision not yet in all Ollama builds) ─
    if _USE_OLLAMA:
        try:
            # Ollama gemma4 supports vision via /api/generate with images
            import base64 as _b64
            from io import BytesIO as _BytesIO
            buf = _BytesIO()
            image.save(buf, format="JPEG", quality=85)
            img_b64 = _b64.b64encode(buf.getvalue()).decode()
            payload = _json.dumps({
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
                "options": {"num_predict": max_new_tokens, "temperature": 0.4, "repeat_penalty": 1.15,
                            "stop": ["<end_of_turn>", "<start_of_turn>"]},
            }).encode()
            req = _urllib_req.Request(
                f"{OLLAMA_URL}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with _urllib_req.urlopen(req, timeout=120) as resp:
                data = _json.loads(resp.read())
                raw = data.get("response", "").replace("<end_of_turn>", "").strip()
                LAST_GEMMA_TRACE["raw"] = raw[:1200]
                LAST_GEMMA_TRACE["path"] = "ollama_multimodal_photo"
                return raw
        except Exception as exc:
            LAST_GEMMA_TRACE["error"] = f"Ollama photo: {exc}"
    # ── Transformers backend ──────────────────────────────────────────────────
    try:
        inputs = processor(text=prompt, images=image, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items() if hasattr(v, "to")}
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                repetition_penalty=1.15,
                eos_token_id=processor.tokenizer.eos_token_id,
                pad_token_id=processor.tokenizer.eos_token_id,
            )
        generated_ids = outputs[0][inputs["input_ids"].shape[-1]:]
        raw = processor.decode(generated_ids, skip_special_tokens=True).replace("<end_of_turn>", "").strip()
        LAST_GEMMA_TRACE["raw"] = raw[:1200]
        return raw
    except Exception as exc:
        LAST_GEMMA_TRACE["error"] = f"{type(exc).__name__}: {exc}"
        LAST_GEMMA_TRACE["fallback_used"] = True
        return ""

def generate_photo_answer(user_text: str, triage: dict, docs: list, language: str, image, quality: dict) -> str:
    lang = normalize_language_name(language)
    if quality.get("quality") == "poor" and len((user_text or "").split()) < 4:
        LAST_GEMMA_TRACE.update({"called": False, "path": "photo_quality_gate", "raw": "", "fallback_used": True, "error": ""})
        return safe_fallback_answer(user_text, {"category": "photo_unclear", "urgency": "LOW"}, docs, lang, image_present=True)
    prompt = build_photo_prompt(user_text, triage, docs, lang, quality)
    raw = call_gemma_photo(prompt, image)
    if raw and not looks_unsafe_photo_answer(raw) and not violates_requested_language(raw, lang):
        return raw[:1800]
    LAST_GEMMA_TRACE["fallback_used"] = True
    return safe_fallback_answer(user_text, triage, docs, lang, image_present=True)


def build_contextual_user_text(user_text: str, conversation_history: list[dict] | None = None) -> tuple[str, str]:
    """Add recent turn context for short follow-up messages.

    Example:
      Turn 1: "my phone is not charging"
      Turn 2: "it is an iPhone 14"
    The second turn becomes contextualized for retrieval/triage.
    """
    text = (user_text or "").strip()
    history = conversation_history or []
    if not history:
        return text, ""

    short_followup = len(norm_text(text).split()) <= 8
    triage_now = triage_issue(text) if text else {"category": "unknown"}
    lacks_signal = triage_now.get("category") in {"unknown", "vague_problem"}

    if short_followup or lacks_signal:
        recent = []
        for turn in history[-3:]:
            u = turn.get("user") or turn.get("customer") or ""
            a = turn.get("assistant") or ""
            if u:
                recent.append(f"Previous customer: {u}")
            if a:
                # Keep assistant context short to avoid prompt bloat.
                recent.append(f"Previous RepairWise summary: {a.splitlines()[0][:160]}")
        context = "\n".join(recent[-4:])
        if context:
            effective = f"{context}\nCurrent customer message: {text}"
            return effective, context

    return text, ""


# ── Conversational follow-up questions ───────────────────────────────────────
# When triage returns vague_problem or unknown, instead of a generic answer
# the system asks a targeted diagnostic question. This creates real conversation.

FOLLOWUP_QUESTIONS = {
    "Spanish": {
        "vague_problem": [
            "Para ayudarte mejor, dime: ¿el móvil no enciende, no carga, tiene la pantalla rota, va lento o falla una app concreta?",
            "Cuéntame más: ¿qué pasa exactamente? ¿Hay algún mensaje de error, se apaga solo, o no responde al tacto?",
        ],
        "unknown": [
            "No he entendido bien el problema. ¿Puedes describir qué le pasa al móvil? Por ejemplo: no enciende, no carga, pantalla rota, va lento...",
        ],
        "boot_issue": [
            "¿El móvil se queda en el logo y no pasa de ahí, o se reinicia solo continuamente? ¿Pasó después de una actualización o de forma repentina?",
        ],
        "charging_issue": [
            "¿No carga nada de nada, carga muy lento, o solo carga si mueves el cable? ¿Has probado con otro cable y cargador?",
        ],
        "screen_repair": [
            "¿La pantalla tiene la imagen pero el táctil no funciona, o la pantalla está completamente apagada? ¿Hay líneas o manchas?",
        ],
    },
    "English": {
        "vague_problem": [
            "To help you better: does the phone not turn on, not charge, have a broken screen, run slowly, or is a specific app failing?",
            "Can you tell me more? Is there an error message, does it shut down randomly, or does the screen not respond?",
        ],
        "unknown": [
            "I didn't quite catch the issue. Can you describe what's happening? For example: won't turn on, not charging, cracked screen, running slow...",
        ],
        "boot_issue": [
            "Is the phone stuck on the logo and won't go past it, or does it keep restarting in a loop? Did this happen after an update or suddenly?",
        ],
        "charging_issue": [
            "Does it not charge at all, charge very slowly, or only charge when you wiggle the cable? Have you tried a different cable and charger?",
        ],
        "screen_repair": [
            "Does the screen show an image but the touch doesn't work, or is the screen completely black? Are there any lines or dark spots?",
        ],
    },
    "Catalan": {
        "vague_problem": [
            "Per ajudar-te millor, digues-me: el mòbil no s'encén, no carrega, té la pantalla trencada, va lent o falla una app concreta?",
        ],
        "unknown": [
            "No he entès bé el problema. Pots descriure què li passa al mòbil?",
        ],
        "boot_issue": [
            "El mòbil es queda al logo i no passa d'aquí, o es reinicia sol contínuament? Va passar després d'una actualització?",
        ],
        "charging_issue": [
            "No carrega gens, carrega molt lent, o només carrega si mous el cable? Has provat amb un altre cable i carregador?",
        ],
    },
    "Arabic": {
        "vague_problem": [
            "لمساعدتك بشكل أفضل، هل الهاتف لا يعمل، لا يشحن، الشاشة مكسورة، بطيء، أم تطبيق معين لا يعمل؟",
        ],
        "unknown": [
            "لم أفهم المشكلة جيداً. هل يمكنك وصف ما يحدث بالضبط؟",
        ],
        "boot_issue": [
            "هل الهاتف عالق عند الشعار ولا يتجاوزه، أم يعيد التشغيل باستمرار؟ هل حدث ذلك بعد تحديث أم فجأة؟",
        ],
    },
    "Romanian": {
        "vague_problem": [
            "Ca să te ajut mai bine, spune-mi: telefonul nu pornește, nu se încarcă, are ecranul spart, merge lent sau o aplicație nu funcționează?",
        ],
        "unknown": [
            "Nu am înțeles bine problema. Poți descrie ce se întâmplă cu telefonul?",
        ],
        "boot_issue": [
            "Telefonul rămâne blocat pe logo și nu trece mai departe, sau repornește continuu singur? S-a întâmplat după o actualizare?",
        ],
    },
    "Urdu": {
        "vague_problem": [
            "بہتر مدد کے لیے بتائیں: فون آن نہیں ہوتا، چارج نہیں ہوتا، اسکرین ٹوٹی ہے، سست چل رہا ہے، یا کوئی ایپ کام نہیں کر رہی؟",
        ],
        "unknown": [
            "مجھے مسئلہ سمجھ نہیں آیا۔ کیا آپ بتا سکتے ہیں کہ فون میں کیا ہو رہا ہے؟",
        ],
        "boot_issue": [
            "فون لوگو پر رک جاتا ہے اور آگے نہیں جاتا، یا بار بار ری اسٹارٹ ہوتا رہتا ہے؟ کیا یہ اپڈیٹ کے بعد ہوا؟",
        ],
    },
}

import random as _random

def get_followup_question(category: str, language: str, history: list) -> str | None:
    """Return a conversational follow-up question when more info is needed.
    
    Returns None if we already asked a question in the last turn (avoid loops).
    """
    lang = normalize_language_name(language)
    questions = FOLLOWUP_QUESTIONS.get(lang, FOLLOWUP_QUESTIONS.get("English", {}))
    options = questions.get(category, questions.get("vague_problem", []))
    if not options:
        return None
    
    # Don't ask follow-up if last assistant turn was already a question
    if history:
        last_assistant = ""
        for turn in reversed(history):
            a = turn.get("assistant") or turn.get("content") if turn.get("role") == "assistant" else ""
            if a:
                last_assistant = str(a)
                break
        if last_assistant.strip().endswith("?"):
            return None  # Already asked, don't loop
    
    return _random.choice(options)

def should_ask_followup(triage: dict, user_text: str, history: list) -> bool:
    """Decide if we should ask a follow-up instead of giving a full answer."""
    category = triage.get("category", "unknown")
    urgency = triage.get("urgency", "LOW")
    
    # Never ask follow-up for HIGH urgency — always give immediate safety advice
    if urgency == "HIGH":
        return False
    
    # Ask follow-up for vague or unknown on first mention
    if category in {"vague_problem", "unknown"}:
        return True
    
    # Ask follow-up for MEDIUM categories if query is very short (< 5 words)
    # and no history exists yet
    if urgency == "MEDIUM" and len(norm_text(user_text).split()) <= 4 and not history:
        return True
    
    return False


# ── Scam confidence scorer ────────────────────────────────────────────────────
# Computes a deterministic phishing probability score from message signals.
# Runs BEFORE Gemma 4 — grounded in rules, not model guessing.

SCAM_SIGNALS = {
    # High weight signals (each +20-25%)
    "data_request":    (["tarjeta", "card", "pin", "contraseña", "password",
                         "clave", "otp", "codigo", "código", "cvv", "cuenta",
                         "account number", "card number", "clau"], 25),
    "suspicious_url":  (["bit.ly", "tinyurl", "http://", ".xyz", ".tk",
                         "secure-", "verify-", "login-", "update-account",
                         "bank-secure", "alert-", "suspended-",
                         "link", "enlace", "url", "haz clic", "click here",
                         "pincha", "pulsa aquí"], 25),
    "impersonation":   (["bbva", "santander", "caixabank", "sabadell", "bankia",
                         "ing", "openbank", "unicaja", "abanca",
                         "paypal", "amazon", "correos", "hacienda",
                         "seguridad social", "dgt", "policia",
                         "banco", "bank", "banca", "banc",
                         "el banco", "mi banco", "your bank", "the bank"], 20),
    "urgency_lang":    (["urgente", "urgent", "inmediatamente", "immediately",
                         "suspendida", "suspended", "bloqueada", "blocked",
                         "24 horas", "24 hours", "ahora mismo", "right now",
                         "o perderá", "or you will lose", "última advertencia"], 20),
    # Medium weight signals (each +10-15%)
    "threatening":     (["cuenta eliminada", "account deleted", "acción legal",
                         "legal action", "multa", "fine", "detenido",
                         "arrested"], 15),
    "free_offer":      (["gratis", "free", "ganado", "won", "premio", "prize",
                         "regalo", "gift", "transferencia gratuita"], 10),
    "grammar_issues":  (["clcik", "verefy", "acccount", "bankk", "urgente!!!!",
                         "click here!!"], 8),
}

def compute_scam_score(text: str) -> dict:
    """Compute phishing probability and detected signals from message text."""
    t = text.lower()
    total_score = 0
    detected = []
    detail = []

    for signal_name, (keywords, weight) in SCAM_SIGNALS.items():
        found_kw = [kw for kw in keywords if kw.lower() in t]
        if found_kw:
            total_score += weight
            detected.append(signal_name)
            detail.append(f"{signal_name}: {found_kw[0]}")

    # Cap at 99% — never 100% certain from text alone
    probability = min(99, total_score)

    # Detect impersonated entity
    entity = "Unknown"
    bank_names = ["bbva", "santander", "caixabank", "sabadell", "bankia",
                  "ing", "openbank", "paypal", "amazon", "correos"]
    for bank in bank_names:
        if bank in t:
            entity = bank.upper()
            break

    verdict = (
        "🔴 VERY LIKELY SCAM" if probability >= 70 else
        "🟡 SUSPICIOUS — verify before acting" if probability >= 40 else
        "🟢 LOW SCAM RISK — but stay cautious"
    )

    return {
        "scam_probability": probability,
        "verdict": verdict,
        "signals_detected": detected,
        "signal_detail": detail,
        "impersonated_entity": entity,
        "signal_count": len(detected),
    }

def format_scam_score_line(score_data: dict, language: str) -> str:
    """Format the scam score as a visible line to prepend to the answer."""
    prob = score_data["scam_probability"]
    verdict = score_data["verdict"]
    entity = score_data["impersonated_entity"]
    signals = score_data["signal_count"]

    labels = {
        "Spanish":  f"📊 Análisis de estafa: {prob}% probabilidad — {verdict}",
        "English":  f"📊 Scam analysis: {prob}% probability — {verdict}",
        "Catalan":  f"📊 Anàlisi d'estafa: {prob}% probabilitat — {verdict}",
        "Arabic":   f"📊 تحليل الاحتيال: {prob}% احتمالية — {verdict}",
        "Romanian": f"📊 Analiză înșelătorie: {prob}% probabilitate — {verdict}",
        "Urdu":     f"📊 فراڈ تجزیہ: {prob}% امکان — {verdict}",
    }
    lang = normalize_language_name(language)
    base = labels.get(lang, labels["English"])
    if entity != "Unknown" and signals > 0:
        base += f" | Impersonating: {entity} | Signals: {signals}"
    return base


# ══════════════════════════════════════════════════════════════════════════════
# CACTUS PRIZE: Intelligent Model Router
# "For the best local-first application that intelligently routes tasks
#  between models" — Gemma 4 Good Hackathon Special Technology Prize
#
# RepairWise uses a 4-tier routing strategy:
#   Tier 0: Deterministic triage (always runs first, no model needed)
#   Tier 1: E2B local (2B params, edge device, <1s response)
#   Tier 2: E4B local (4B params, better quality for complex queries)
#   Tier 3: Template fallback (offline, zero model dependency)
#
# The router decides which tier to use based on:
#   - Query complexity score
#   - Available hardware (GPU VRAM)
#   - Urgency level (HIGH → always fast E2B)
#   - Language complexity (RTL scripts → may need more capacity)
#   - Context length (multi-turn → needs more tokens)
# ══════════════════════════════════════════════════════════════════════════════

import os as _os_router

# Model tier configuration
ROUTER_CONFIG = {
    "e2b": {
        "model_id": "google/gemma-4-e2b",
        "ollama_model": "gemma4:e2b",
        "params": "2B",
        "vram_gb": 4,
        "max_tokens": 300,
        "latency": "fast",
        "use_cases": ["simple_repair", "scam_detection", "follow_up"],
        "description": "Edge model — fast, fits on device",
    },
    "e4b": {
        "model_id": "google/gemma-4-e4b",
        "ollama_model": "gemma4:e4b",
        "params": "4B",
        "vram_gb": 8,
        "max_tokens": 512,
        "latency": "medium",
        "use_cases": ["complex_diagnosis", "multilingual_nuanced", "multi_symptom"],
        "description": "4B model — better quality for complex queries",
    },
    "template": {
        "model_id": None,
        "ollama_model": None,
        "params": "0",
        "vram_gb": 0,
        "max_tokens": 0,
        "latency": "instant",
        "use_cases": ["high_urgency_safety", "offline", "no_gpu"],
        "description": "Deterministic — zero latency, no model",
    },
}

# E4B Ollama model tag (separate from E2B)
OLLAMA_MODEL_E4B = _os_router.environ.get("OLLAMA_MODEL_E4B", "gemma4:e4b")

def _call_e4b_via_ollama(prompt: str, max_tokens: int = 450) -> str:
    """Call E4B model via Ollama for complex queries.
    
    This is the key Cactus routing: complex queries go to E4B (4B params)
    instead of E2B (2B params), giving higher quality at the cost of speed.
    Falls back to E2B if E4B is not available.
    """
    # Try E4B first
    payload = _json.dumps({
        "model": OLLAMA_MODEL_E4B,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.35,   # slightly lower for E4B — more reliable
            "repeat_penalty": 1.10,
            "stop": ["<end_of_turn>", "<start_of_turn>"],
        }
    }).encode()
    try:
        req = _urllib_req.Request(
            f"{OLLAMA_URL}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urllib_req.urlopen(req, timeout=90) as resp:
            data = _json.loads(resp.read())
            raw = data.get("response", "").replace("<end_of_turn>", "").strip()
            if raw:
                LAST_ROUTER_DECISION["actual_model_called"] = OLLAMA_MODEL_E4B
                return raw
    except Exception:
        pass
    # E4B not available — fall back to E2B with richer prompt
    LAST_ROUTER_DECISION["actual_model_called"] = f"{OLLAMA_MODEL} (E4B fallback)"
    return _ollama_chat(prompt, max_tokens=max_tokens)


# Routing decision log (visible in judge panel)
LAST_ROUTER_DECISION = {
    "selected_tier": "template",
    "reason": "",
    "complexity_score": 0,
    "factors": [],
}

def compute_query_complexity(text: str, triage: dict, history: list,
                              language: str) -> dict:
    """
    Score query complexity 0-100 to decide which model tier to use.
    
    Factors:
    - Word count and sentence structure
    - Multiple symptoms mentioned
    - Ambiguous/vague problem
    - RTL language complexity
    - Conversation depth (multi-turn)
    - Technical terminology
    """
    t = norm_text(text)
    words = t.split()
    score = 0
    factors = []

    # Factor 1: Query length
    if len(words) > 20:
        score += 20
        factors.append(f"long_query({len(words)}w)")
    elif len(words) > 10:
        score += 10
        factors.append(f"medium_query({len(words)}w)")

    # Factor 2: Multiple symptoms — only count if real symptom words present
    # Avoid false positives from generic conjunctions like "y" or "and"
    symptom_indicators = [
        "también", "also", "además", "a més", "و", "بھی", "și",
        "plus", "another", "otro", "altra", "another problem",
        "y también", "and also", "pero también",
    ]
    symptom_count = sum(1 for w in symptom_indicators if w in t)
    if symptom_count >= 1:
        score += 15
        factors.append(f"multi_symptom({symptom_count})")

    # Factor 3: Vague or unknown category
    if triage.get("category") in {"vague_problem", "unknown"}:
        score += 20
        factors.append("vague_category")

    # Factor 4: Multi-turn conversation depth
    turns = len(history or []) // 2
    if turns >= 3:
        score += 20
        factors.append(f"deep_conversation({turns}turns)")
    elif turns >= 1:
        score += 10
        factors.append(f"multi_turn({turns}turns)")

    # Factor 5: RTL language (Arabic, Urdu) — more nuanced output needed
    lang = normalize_language_name(language)
    if lang in {"Arabic", "Urdu"}:
        score += 15
        factors.append(f"rtl_language({lang})")

    # Factor 6: Technical question (warranty, data recovery, privacy)
    technical_cats = {"data_recovery", "privacy_repair", "warranty",
                      "update_issue", "sim_network_issue"}
    if triage.get("category") in technical_cats:
        score += 15
        factors.append("technical_category")

    return {"score": min(100, score), "factors": factors}

def select_model_tier(complexity: dict, triage: dict, has_image: bool,
                       demo_mode: bool) -> str:
    """
    Intelligent routing decision — the core of the Cactus implementation.
    
    Returns: "template" | "e2b" | "e4b"
    """
    score = complexity["score"]
    urgency = triage.get("urgency", "LOW")
    category = triage.get("category", "unknown")
    factors = []

    # Rule 1: Safety critical → always template (fastest, most reliable)
    if urgency == "HIGH" and category in {"battery_safety", "water_damage"}:
        reason = "HIGH urgency safety — template guarantees immediate response"
        LAST_ROUTER_DECISION.update({
            "selected_tier": "template",
            "reason": reason,
            "complexity_score": score,
            "factors": complexity["factors"] + ["safety_override"],
        })
        return "template"

    # Rule 2: No model available → template
    if demo_mode or model is None:
        reason = "No GPU/model available — template fallback"
        LAST_ROUTER_DECISION.update({
            "selected_tier": "template",
            "reason": reason,
            "complexity_score": score,
            "factors": complexity["factors"] + ["no_model"],
        })
        return "template"

    # Rule 3: Image present → always E2B (multimodal)
    if has_image:
        reason = "Photo analysis — E2B multimodal vision"
        LAST_ROUTER_DECISION.update({
            "selected_tier": "e2b",
            "reason": reason,
            "complexity_score": score,
            "factors": complexity["factors"] + ["multimodal_photo"],
        })
        return "e2b"

    # Rule 4: High complexity → E4B if available, else E2B
    if score >= 60:
        # Check if E4B is loaded (future-proof)
        tier = "e4b" if _os_router.environ.get("REPAIRWISE_E4B_AVAILABLE") else "e2b"
        reason = f"High complexity ({score}/100) → {tier.upper()} for quality"
        LAST_ROUTER_DECISION.update({
            "selected_tier": tier,
            "reason": reason,
            "complexity_score": score,
            "factors": complexity["factors"],
        })
        return tier

    # Rule 5: Medium complexity → E2B
    if score >= 25:
        reason = f"Medium complexity ({score}/100) → E2B balanced"
        LAST_ROUTER_DECISION.update({
            "selected_tier": "e2b",
            "reason": reason,
            "complexity_score": score,
            "factors": complexity["factors"],
        })
        return "e2b"

    # Rule 6: Simple, low urgency → E2B fast path
    reason = f"Simple query ({score}/100) → E2B fast path"
    LAST_ROUTER_DECISION.update({
        "selected_tier": "e2b",
        "reason": reason,
        "complexity_score": score,
        "factors": complexity["factors"] + ["simple_fast_path"],
    })
    return "e2b"

def get_router_summary() -> str:
    """Format routing decision for judge panel display."""
    d = LAST_ROUTER_DECISION
    tier = d.get("selected_tier", "unknown").upper()
    score = d.get("complexity_score", 0)
    reason = d.get("reason", "")
    factors = d.get("factors", [])
    return (
        f"CACTUS ROUTER\n"
        f"  Selected: {tier}\n"
        f"  Complexity: {score}/100\n"
        f"  Reason: {reason[:80]}\n"
        f"  Factors: {factors}"
    )


# ── One-line recommendations per category + language ─────────────────────────
# Shown prominently between Risk level and detailed steps.
# Designed for elderly users and people with limited digital literacy:
# ONE clear action, in their language, in bold.

RECOMMENDATIONS = {
    "scam_phishing": {
        "English":  "🚨 DO NOT click the link or enter any codes — this is a phishing scam.",
        "Spanish":  "🚨 NO abras el enlace ni pongas ningún código — es una estafa.",
        "Catalan":  "🚨 NO obris l'enllaç ni possis cap codi — és una estafa.",
        "Arabic":   "🚨 لا تفتح الرابط ولا تُدخل أي رموز — هذا احتيال.",
        "Romanian": "🚨 NU deschide linkul și nu introduce niciun cod — este o înșelătorie.",
        "Urdu":     "🚨 لنک نہ کھولیں اور کوئی کوڈ نہ ڈالیں — یہ فراڈ ہے۔",
    },
    "scam_clicked_link": {
        "English":  "🚨 Close the browser NOW — then change passwords from a different device.",
        "Spanish":  "🚨 Cierra el navegador AHORA — cambia contraseñas desde OTRO dispositivo.",
        "Catalan":  "🚨 Tanca el navegador ARA — canvia contrasenyes des d'un altre dispositiu.",
        "Arabic":   "🚨 أغلق المتصفح الآن — غيّر كلمات المرور من جهاز آخر.",
        "Romanian": "🚨 Închide browserul ACUM — schimbă parolele de pe un alt dispozitiv.",
        "Urdu":     "🚨 ابھی براؤزر بند کریں — دوسرے ڈیوائس سے پاسورڈ بدلیں۔",
    },
    "scam_data_entered": {
        "English":  "🆘 CALL YOUR BANK RIGHT NOW — your card and data may be compromised.",
        "Spanish":  "🆘 LLAMA A TU BANCO AHORA MISMO — tus datos y tarjeta pueden estar comprometidos.",
        "Catalan":  "🆘 TRUCA AL BANC ARA MATEIX — les teves dades i targeta poden estar compromeses.",
        "Arabic":   "🆘 اتصل بالبنك الآن فوراً — بياناتك وبطاقتك قد تكون في خطر.",
        "Romanian": "🆘 SUNĂ BANCA ACUM — datele și cardul tău pot fi compromise.",
        "Urdu":     "🆘 ابھی بینک کو کال کریں — آپ کا ڈیٹا اور کارڈ خطرے میں ہو سکتا ہے۔",
    },
    "battery_safety": {
        "English":  "⚠️ STOP using the phone NOW — a swollen battery is a fire risk.",
        "Spanish":  "⚠️ DEJA de usar el móvil AHORA — la batería hinchada es un riesgo de incendio.",
        "Catalan":  "⚠️ DEIXA d'usar el mòbil ARA — la bateria inflada és un risc d'incendi.",
        "Arabic":   "⚠️ أوقف استخدام الهاتف الآن — البطارية المنتفخة خطر حريق.",
        "Romanian": "⚠️ OPREȘTE imediat telefonul — o baterie umflată este risc de incendiu.",
        "Urdu":     "⚠️ ابھی فون استعمال کرنا بند کریں — پھولی بیٹری آگ کا خطرہ ہے۔",
    },
    "water_damage": {
        "English":  "⚠️ Turn OFF the phone and do NOT charge it — water + electricity is dangerous.",
        "Spanish":  "⚠️ APAGA el móvil y NO lo cargues — agua + electricidad es peligroso.",
        "Catalan":  "⚠️ APAGA el mòbil i NO el carreguis — aigua + electricitat és perillós.",
        "Arabic":   "⚠️ أوقف الهاتف فوراً ولا تشحنه — الماء والكهرباء معاً خطير.",
        "Romanian": "⚠️ OPREȘTE telefonul și NU-l încărca — apa + electricitate este periculos.",
        "Urdu":     "⚠️ فون بند کریں اور چارج نہ کریں — پانی اور بجلی خطرناک ہے۔",
    },
    "overheating_issue": {
        "English":  "⚠️ Turn OFF the phone and let it cool down — do not charge it now.",
        "Spanish":  "⚠️ APAGA el móvil y deja que se enfríe — no lo cargues ahora.",
        "Catalan":  "⚠️ APAGA el mòbil i deixa'l refredar — no el carreguis ara.",
        "Arabic":   "⚠️ أوقف الهاتف واتركه يبرد — لا تشحنه الآن.",
        "Romanian": "⚠️ OPREȘTE telefonul și lasă-l să se răcească — nu-l încărca acum.",
        "Urdu":     "⚠️ فون بند کریں اور ٹھنڈا ہونے دیں — ابھی چارج نہ کریں۔",
    },
    "screen_repair": {
        "English":  "📋 Book a screen repair — avoid pressing the cracked area to prevent further damage.",
        "Spanish":  "📋 Lleva el móvil a reparar la pantalla — no presiones la zona agrietada.",
        "Catalan":  "📋 Porta el mòbil a reparar la pantalla — no pressionis la zona esquerdada.",
        "Arabic":   "📋 اصطحب الهاتف لإصلاح الشاشة — تجنب الضغط على المنطقة المكسورة.",
        "Romanian": "📋 Du telefonul la reparat ecranul — evită să apeși pe zona crăpată.",
        "Urdu":     "📋 اسکرین مرمت کروائیں — ٹوٹی جگہ دبائیں نہیں۔",
    },
    "charging_issue": {
        "English":  "📋 Try a different cable and charger first — if still failing, see a technician.",
        "Spanish":  "📋 Prueba otro cable y cargador primero — si sigue fallando, ve a un técnico.",
        "Catalan":  "📋 Prova un altre cable i carregador primer — si continua fallant, visita un tècnic.",
        "Arabic":   "📋 جرب كابلاً وشاحناً مختلفاً أولاً — إذا استمرت المشكلة اذهب لتقني.",
        "Romanian": "📋 Încearcă un alt cablu și încărcător — dacă tot nu merge, mergi la un tehnician.",
        "Urdu":     "📋 پہلے مختلف کیبل اور چارجر آزمائیں — پھر بھی نہ ہو تو تکنیشن کے پاس جائیں۔",
    },
    "boot_issue": {
        "English":  "📋 Force restart first — hold Power + Volume Down for 10 seconds.",
        "Spanish":  "📋 Haz un reinicio forzado primero — mantén Encendido + Bajar volumen 10 segundos.",
        "Catalan":  "📋 Fes un reinici forçat primer — mantén Engegar + Baixar volum 10 segons.",
        "Arabic":   "📋 أعد التشغيل قسراً أولاً — اضغط الطاقة + خفض الصوت 10 ثوانٍ.",
        "Romanian": "📋 Fă un restart forțat — ține apăsat Power + Volum jos 10 secunde.",
        "Urdu":     "📋 پہلے فورسڈ ری اسٹارٹ کریں — پاور + والیوم ڈاؤن 10 سیکنڈ دبائیں۔",
    },
    "wifi_issue": {
        "English":  "✅ Restart the router and toggle airplane mode — usually fixes WiFi issues.",
        "Spanish":  "✅ Reinicia el router y activa/desactiva el modo avión — suele solucionar el WiFi.",
        "Catalan":  "✅ Reinicia el router i activa/desactiva el mode avió — sol solucionar el WiFi.",
        "Arabic":   "✅ أعد تشغيل الراوتر وفعّل/ألغِ وضع الطيران — يحل مشاكل WiFi عادةً.",
        "Romanian": "✅ Repornește routerul și activează/dezactivează modul avion.",
        "Urdu":     "✅ روٹر ری اسٹارٹ کریں اور ایئرپلین موڈ آن/آف کریں۔",
    },
    "app_issue": {
        "English":  "✅ Force-close the app, clear its cache, then reopen — fixes most app crashes.",
        "Spanish":  "✅ Cierra la app completamente, borra su caché y vuelve a abrirla.",
        "Catalan":  "✅ Tanca l'app completament, esborra la seva memòria cau i torna a obrir-la.",
        "Arabic":   "✅ أغلق التطبيق بالكامل، امسح ذاكرته المؤقتة، ثم أعد فتحه.",
        "Romanian": "✅ Închide complet aplicația, șterge cache-ul și redeschide-o.",
        "Urdu":     "✅ ایپ مکمل بند کریں، کیشے صاف کریں، پھر دوبارہ کھولیں۔",
    },
    "storage_issue": {
        "English":  "✅ Delete unused apps and old photos — free up at least 2GB for stability.",
        "Spanish":  "✅ Elimina apps y fotos antiguas — libera al menos 2GB para estabilidad.",
        "Catalan":  "✅ Elimina apps i fotos antigues — allibera almenys 2GB per a estabilitat.",
        "Arabic":   "✅ احذف التطبيقات والصور القديمة — حرر 2GB على الأقل للاستقرار.",
        "Romanian": "✅ Șterge aplicații și poze vechi — eliberează cel puțin 2GB.",
        "Urdu":     "✅ پرانی ایپس اور تصاویر حذف کریں — کم از کم 2GB خالی کریں۔",
    },
    "data_recovery": {
        "English":  "📋 Do NOT factory reset yet — first try Google/iCloud backup restore.",
        "Spanish":  "📋 NO hagas restablecimiento de fábrica todavía — prueba primero restaurar desde copia de seguridad.",
        "Catalan":  "📋 NO facis restabliment de fàbrica encara — prova primer restaurar des de còpia de seguretat.",
        "Arabic":   "📋 لا تعيد ضبط المصنع بعد — جرب أولاً استعادة النسخ الاحتياطية.",
        "Romanian": "📋 NU face resetare la fabrică încă — încearcă mai întâi restaurarea din backup.",
        "Urdu":     "📋 ابھی فیکٹری ری سیٹ نہ کریں — پہلے بیک اپ سے بحالی آزمائیں۔",
    },
    "vague_problem": {
        "English":  "💬 Tell me more — what exactly happens when you use the phone?",
        "Spanish":  "💬 Cuéntame más — ¿qué pasa exactamente cuando usas el móvil?",
        "Catalan":  "💬 Explica'm més — Què passa exactament quan fas servir el mòbil?",
        "Arabic":   "💬 أخبرني أكثر — ماذا يحدث بالضبط عند استخدام الهاتف؟",
        "Romanian": "💬 Spune-mi mai multe — ce se întâmplă exact când folosești telefonul?",
        "Urdu":     "💬 مزید بتائیں — فون استعمال کرتے وقت کیا ہوتا ہے؟",
    },
}

DEFAULT_RECOMMENDATIONS = {
    "English":  "📋 Check the steps below carefully — if in doubt, consult a technician.",
    "Spanish":  "📋 Revisa los pasos a continuación — si tienes dudas, consulta a un técnico.",
    "Catalan":  "📋 Revisa els passos a continuació — si tens dubtes, consulta un tècnic.",
    "Arabic":   "📋 راجع الخطوات أدناه — إذا كنت في شك فاستشر فنياً.",
    "Romanian": "📋 Verifică pașii de mai jos — dacă ai dubii, consultă un tehnician.",
    "Urdu":     "📋 نیچے دیے گئے اقدامات دیکھیں — شک ہو تو تکنیشن سے پوچھیں۔",
}

def get_recommendation(category: str, language: str) -> str:
    """Get the one-line recommendation for a category in the given language."""
    lang = normalize_language_name(language)
    cat_recs = RECOMMENDATIONS.get(category, {})
    return cat_recs.get(lang, DEFAULT_RECOMMENDATIONS.get(lang,
           DEFAULT_RECOMMENDATIONS["English"]))


# ══════════════════════════════════════════════════════════════════════════════
# UNIVERSAL CONVERSATIONAL CONTEXT SYSTEM
# Every category supports multi-turn conversation.
# When the user sends a short follow-up, the system inherits the previous
# category and responds in context instead of starting over.
# ══════════════════════════════════════════════════════════════════════════════

# Keywords that signal each category — used to detect prev context
CATEGORY_CONTEXT_SIGNALS = {
    "scam_phishing":        ["phishing","estafa","scam","enlace","link","sms","banco","bank","tarjeta","otp"],
    "battery_safety":       ["batería","battery","hinchada","swollen","bulging","inflada","levanta","lifting"],
    "water_damage":         ["agua","water","mojado","wet","cayó al agua","dropped in water","lluvia"],
    "overheating_issue":    ["caliente","hot","calor","sobrecalenta","overheating","se calienta","burns"],
    "charging_issue":       ["carga","charging","cargador","charger","cable","no carga","not charging"],
    "screen_repair":        ["pantalla","screen","display","rota","cracked","broken","táctil","touch"],
    "boot_issue":           ["enciende","arranca","logo","bootloop","reinicia","restart","start","encén"],
    "sim_network_issue":    ["sim","señal","signal","red","network","cobertura","coverage","llamadas"],
    "app_issue":            ["app","aplicación","application","crashes","falla","no abre","freezes"],
    "storage_issue":        ["almacenamiento","storage","lleno","full","espacio","space","memoria"],
    "wifi_issue":           ["wifi","wi-fi","internet","conexión","connection","router","bluetooth"],
    "update_issue":         ["actualización","update","sistema","android","ios","upgrade","version"],
    "camera_issue":         ["cámara","camera","foto","photo","picture","borrosa","blurry","flash"],
    "audio_issue":          ["audio","sonido","sound","altavoz","speaker","micrófono","mic","calls"],
    "data_recovery":        ["datos","data","perdido","lost","borrado","deleted","recuperar","recover"],
    "battery_drain":        ["batería se gasta","battery drains","dura poco","doesn't last","agota"],
    "privacy_repair":       ["privacidad","privacy","datos personales","contraseña","técnico","repair shop"],
    "warranty":             ["garantía","warranty","garantia","devolver","return","devolución","refund"],
    "scam_clicked_link":    ["abrí","abri","clic","click","pulsé","opened","clicked","entré","entered"],
}

# Short follow-up phrases that inherit previous context
FOLLOW_UP_TRIGGERS = {
    "Spanish":  ["que hago", "qué hago", "ahora qué", "y ahora", "cómo lo hago",
                 "cómo", "como", "y si", "funciona", "sigo", "después", "luego",
                 "ok", "vale", "bien", "gracias", "y", "siguiente", "qué más",
                 "me ayudas", "ayuda", "no entiendo", "no funciona", "sigue igual",
                 "no ha cambiado", "lo apagué", "lo hice", "ya lo hice", "listo",
                 "hecho", "hice", "probé", "intenté", "ya reinicié"],
    "English":  ["what now", "what do i", "how do i", "now what", "and now",
                 "ok thanks", "done", "i did it", "tried it", "still not",
                 "doesn't work", "still same", "next step", "what else",
                 "i turned it off", "i restarted", "didn't work", "help"],
    "Catalan":  ["que faig", "ara que", "i ara", "com ho faig", "funciona",
                 "ho he fet", "ja ho he", "i si", "gràcies", "no funciona"],
    "Arabic":   ["ماذا أفعل", "والآن", "ثم ماذا", "كيف", "جربت", "لم ينجح"],
    "Romanian": ["ce fac", "și acum", "cum", "am făcut", "nu merge", "ajutor"],
    "Urdu":     ["اب کیا", "کیسے", "کیا کروں", "ہو گیا", "نہیں ہوا", "مدد"],
}

def detect_conversation_context(text: str, history: list, language: str) -> dict | None:
    """
    Detect if this is a follow-up to a previous turn.
    Returns the inherited triage dict or None if this is a fresh query.
    """
    if not history or len(history) < 2:
        return None

    t = norm_text(text)
    words = t.split()

    # Only inherit for SHORT queries (≤ 8 words)
    # Long queries likely contain new info and should be re-triaged
    if len(words) > 8:
        return None

    # Check if text is a follow-up trigger phrase
    lang = normalize_language_name(language)
    triggers = FOLLOW_UP_TRIGGERS.get(lang, FOLLOW_UP_TRIGGERS["English"])
    is_followup_phrase = any(trigger in t for trigger in triggers)

    # Check for NEW category signals in the text
    # If text mentions a DIFFERENT category than the previous one, don't inherit
    prev_cat = None
    for turn in reversed(history):
        content = turn.get("content", "").lower()
        for cat, signals in CATEGORY_CONTEXT_SIGNALS.items():
            if any(sig in content for sig in signals):
                prev_cat = cat
                break
        if prev_cat:
            break

    new_cat_signals = [
        cat for cat, signals in CATEGORY_CONTEXT_SIGNALS.items()
        if any(sig in t for sig in signals) and cat != prev_cat
    ]
    has_different_category = len(new_cat_signals) > 0

    # If user introduces a NEW different category topic, don't inherit
    if has_different_category and not is_followup_phrase:
        return None

    # Find the most recent category from history
    prev_category = None
    prev_urgency = "LOW"
    for turn in reversed(history):
        content = turn.get("content", "").lower()
        for cat, signals in CATEGORY_CONTEXT_SIGNALS.items():
            if any(sig in content for sig in signals):
                prev_category = cat
                # Estimate urgency from content
                if any(x in content for x in ["high 🔴", "high", "urgente", "urgent", "danger", "peligro"]):
                    prev_urgency = "HIGH"
                elif any(x in content for x in ["medium 🟡", "medium", "medio"]):
                    prev_urgency = "MEDIUM"
                break
        if prev_category:
            break

    if not prev_category:
        return None

    return {
        "category": prev_category,
        "urgency": prev_urgency,
        "reason": f"Follow-up to {prev_category} conversation.",
        "match_type": "conversation_inherited",
        "inherited_from": prev_category,
    }


def get_followup_response(triage: dict, text: str, language: str, history: list) -> str | None:
    """
    Generate a context-aware follow-up response.
    Returns a string if a specific follow-up response is appropriate, None otherwise.
    """
    cat = triage.get("category", "")
    lang = normalize_language_name(language)
    t = norm_text(text)

    # "Already did X" confirmations
    done_words = ["apagué", "apague", "reinicié", "reinicie", "hice", "probé", "probe",
                  "turned off", "restarted", "tried", "done", "lo hice", "ya lo hice",
                  "i did", "listo", "hecho", "ho he fet", "ya reinicié"]

    if any(w in t for w in done_words):
        responses = {
            "overheating_issue": {
                "Spanish": "Bien. Ahora espera al menos 15-20 minutos antes de encenderlo. Si vuelve a calentarse al usarlo con normalidad, llévalo a un técnico — puede ser la batería o el procesador.",
                "English": "Good. Wait at least 15-20 minutes before turning it back on. If it overheats again during normal use, see a technician — it may be the battery or processor.",
                "Catalan": "Bé. Ara espera almenys 15-20 minuts abans d'encendre'l. Si torna a escalfar-se, porta'l a un tècnic.",
            },
            "battery_safety": {
                "Spanish": "Muy bien. No lo enciendas — llévalo a un técnico hoy mismo. Una batería hinchada es un riesgo de incendio real.",
                "English": "Good. Do not turn it on — take it to a technician today. A swollen battery is a real fire risk.",
            },
            "charging_issue": {
                "Spanish": "¿Ahora está cargando? Si sigue sin cargar, prueba a limpiar el puerto con un palillo de madera suavemente. Si aún no, el puerto puede estar dañado.",
                "English": "Is it charging now? If still not charging, try gently cleaning the port with a wooden toothpick. If still nothing, the port may be damaged.",
            },
            "water_damage": {
                "Spanish": "Perfecto. Déjalo en arroz o con gel de sílice 48 horas — no lo enciendas antes. Si hay agua dentro, encenderlo puede cortocircuitarlo.",
                "English": "Perfect. Leave it in rice or silica gel for 48 hours — don't turn it on yet. Water inside can short-circuit it if powered on.",
            },
            "boot_issue": {
                "Spanish": "¿Arrancó? Si sigue en el logo, prueba el modo seguro: apaga, mantén el botón de bajar volumen al encender. Si no arranca, puede ser una actualización corrupta.",
                "English": "Did it boot? If still stuck on logo, try safe mode: hold volume down while powering on. If still nothing, it may be a corrupted update.",
            },
            "scam_phishing": {
                "Spanish": "Bien hecho. Ahora activa las alertas de tu banco por SMS y revisa los últimos movimientos. Si ves algo extraño, llama inmediatamente.",
                "English": "Good. Now enable bank SMS alerts and review recent transactions. If anything looks unusual, call your bank immediately.",
            },
        }
        cat_resp = responses.get(cat, {})
        return cat_resp.get(lang, cat_resp.get("English", None))

    # "Still not working" frustration responses  
    still_bad = ["no funciona", "sigue igual", "no ha cambiado", "still same",
                 "doesn't work", "still not", "no ha servido", "no sirve",
                 "segueix igual", "no ha funcionat"]
    if any(w in t for w in still_bad):
        responses = {
            "Spanish": {
                "overheating_issue": "Si sigue calentándose después de reiniciarlo, el problema puede ser la batería o el procesador. Llévalo a un técnico — no lo fuerces más.",
                "charging_issue": "Si has probado otro cable y cargador y sigue sin cargar, el puerto está dañado. Necesita reparación profesional.",
                "boot_issue": "Si sigue bloqueado en el logo después del reinicio forzado, prueba el modo de recuperación. Pero si hay datos importantes, mejor ve a un técnico antes de intentar nada más.",
                "wifi_issue": "Si reiniciaste el router y el móvil y sigue sin conectar, prueba a olvidar la red WiFi y reconectarte. Si no, puede ser un problema de hardware.",
                "app_issue": "Si borraste la caché y sigue fallando, desinstala y reinstala la app. Si el problema es con varias apps, puede ser almacenamiento lleno o actualización del sistema.",
            },
        }
        lang_resp = responses.get(lang, responses.get("Spanish", {}))
        return lang_resp.get(cat, None)

    return None
def repairwise_answer(
    user_text: str,
    language: str = "Spanish",
    image=None,
    return_meta: bool = False,
    conversation_history: list[dict] | None = None,
):
    reset_gemma_trace()
    lang = normalize_language_name(language)
    original_text = (user_text or "").strip()
    text, history_context = build_contextual_user_text(original_text, conversation_history)

    if image is not None:
        if not text:
            text = "Customer sent a photo of a phone problem."

        quality = image_quality_report(image)
        visual_description = describe_image_with_gemma(image, lang)
        photo_text = text
        if visual_description:
            photo_text = f"{text}\nVisible image description from Gemma 4: {visual_description}"

        hint = classify_photo_intent_from_text(photo_text)
        triage = triage_issue(photo_text)
        if hint["score"] > 0 or triage["category"] in {"unknown", "vague_problem"}:
            triage = {
                "urgency": hint["risk"],
                "category": hint["repair_category"],
                "reason": f"Photo mode visual hint: {hint['visual_category']}; image_description={visual_description[:120]}",
                "method": "v16_photo_multimodal_description",
                "confidence": 0.93 if visual_description else 0.90,
                "visual_category": hint["visual_category"],
            }

        docs = photo_docs_for_category(triage["category"], hint["visual_category"]) + retrieve_knowledge(photo_text, k=5, category=triage["category"], image_present=True)
        unique_docs = []
        seen = set()
        for d in docs:
            if d.get("id") not in seen:
                unique_docs.append(d)
                seen.add(d.get("id"))
        docs = unique_docs[:6]

        answer = generate_photo_answer(photo_text, triage, docs[:4], lang, image, quality)
        # Add Cactus router info for image path
        img_complexity = compute_query_complexity(
            photo_text, triage, history_context or [], lang
        )
        select_model_tier(img_complexity, triage, has_image=True, demo_mode=DEMO_MODE)

        meta = {
            "version": REPAIRWISE_VERSION,
            "scam_analysis": None,
            "cactus_router": LAST_ROUTER_DECISION.copy(),
            "triage": triage,
            "sources": [{"id": d.get("id"), "category": d.get("category"), "risk": d.get("risk"), "score": round(float(d.get("score", 0)), 3), "engine_scores": d.get("engine_scores", {})} for d in docs[:5]],
            "context_sufficient": True,
            "photo_mode": True,
            "image_quality": quality,
            "image_description": visual_description,
            "language": lang,
            "effective_text": photo_text,
            "history_used": bool(history_context),
            "gemma": dict(LAST_GEMMA_TRACE),
            "retrieval": {
                "semantic_embedding_available": bool(EMBEDDING_AVAILABLE),
                "semantic_embedding_error": EMBEDDING_ERROR,
            },
        }
        return (answer, meta) if return_meta else answer

    if not original_text:
        answer = "Please describe the phone problem or upload a photo/screenshot."
        return (answer, {}) if return_meta else answer

    # Reset router state for this call
    LAST_ROUTER_DECISION.update({
        "selected_tier": "template", "reason": "", 
        "complexity_score": 0, "factors": []
    })

    # Use original_text for triage — not enriched text which breaks context detection
    triage = triage_issue(original_text, conversation_history=conversation_history)
    # Upgrade scam_phishing → scam_clicked_link if context shows user already clicked
    if triage.get("category") == "scam_phishing" and conversation_history:
        # Check if any previous turn had scam_clicked_link or click language
        for prev in conversation_history:
            prev_content = prev.get("content", "").lower()
            if any(x in prev_content for x in ["abierto", "abri", "clic", "click",
                                                 "opened", "clicked", "scam_clicked"]):
                triage = dict(triage)
                triage["category"] = "scam_clicked_link"
                triage["reason"] = "Context: user previously opened phishing link."
                break
    docs = retrieve_knowledge(text, k=7, category=triage["category"], image_present=False)

    # ── Scam confidence score (injected for phishing queries) ─────────────────
    scam_score_data = None
    if triage.get("category") == "scam_phishing":
        scam_score_data = compute_scam_score(original_text)

    # ── Cactus: Intelligent model routing ────────────────────────────────────
    complexity = compute_query_complexity(text, triage, conversation_history or [], lang)
    selected_tier = select_model_tier(
        complexity, triage, has_image=False, demo_mode=DEMO_MODE
    )
    LAST_GEMMA_TRACE["router"] = get_router_summary()

    # ── Conversational follow-up ─────────────────────────────────────────────
    # Check for specific follow-up response (e.g. "lo apagué", "sigue igual")
    conv_followup_response = None
    if conversation_history and triage.get("match_type") == "conversation_inherited":
        conv_followup_response = get_followup_response(
            triage, original_text, lang, conversation_history
        )

    followup = None
    if should_ask_followup(triage, original_text, conversation_history or []):
        followup = get_followup_question(triage["category"], lang, conversation_history or [])

    if conv_followup_response:
        answer = conv_followup_response
        LAST_GEMMA_TRACE["path"] = "conversational_followup_specific"
        LAST_GEMMA_TRACE["called"] = False
    elif followup:
        answer = followup
        LAST_GEMMA_TRACE["path"] = "conversational_followup"
        LAST_GEMMA_TRACE["called"] = False
    elif selected_tier == "template":
        # Fastest path — no model call, guaranteed safe response
        answer = safe_fallback_answer(text, triage, docs[:3], lang, image_present=False)
        LAST_GEMMA_TRACE["path"] = "cactus_template_tier"
        LAST_GEMMA_TRACE["called"] = False
    else:
        # E2B or E4B path — full model generation
        answer = generate_text_answer(text, triage, docs[:4], lang)
        LAST_GEMMA_TRACE["cactus_tier"] = selected_tier
        if looks_bad_output(answer) or violates_requested_language(answer, lang) or answer_conflicts_with_category(answer, triage["category"], text):
            LAST_GEMMA_TRACE["fallback_used"] = True
            answer = safe_fallback_answer(text, triage, docs[:3], lang, image_present=False)
            tool_result = LAST_GEMMA_TRACE.get("function_calling", {}).get("tool_result", {})
            answer = inject_tool_next_step(answer, tool_result, lang)

    # Prepend scam score to answer if phishing detected
    if scam_score_data and scam_score_data["scam_probability"] >= 30:
        score_line = format_scam_score_line(scam_score_data, lang)
        answer = score_line + "\n\n" + answer
        LAST_GEMMA_TRACE["scam_score"] = scam_score_data

    meta = {
        "version": REPAIRWISE_VERSION,
        "scam_analysis": scam_score_data,
        "cactus_router": LAST_ROUTER_DECISION.copy(),
        "triage": triage,
        "sources": [{"id": d.get("id"), "category": d.get("category"), "risk": d.get("risk"), "score": round(float(d.get("score", 0)), 3), "engine_scores": d.get("engine_scores", {})} for d in docs[:5]],
        "context_sufficient": is_context_sufficient(docs, triage["category"]),
        "photo_mode": False,
        "language": lang,
        "effective_text": text,
        "history_used": bool(history_context),
        "followup_asked": bool(followup),
        "gemma": dict(LAST_GEMMA_TRACE),
        "retrieval": {
            "semantic_embedding_available": bool(EMBEDDING_AVAILABLE),
            "semantic_embedding_error": EMBEDDING_ERROR,
        },
    }
    return (answer, meta) if return_meta else answer

def repairwise_debug(user_text: str, language: str = "Spanish", image=None, conversation_history: list[dict] | None = None):
    return repairwise_answer(user_text, language=language, image=image, return_meta=True, conversation_history=conversation_history)

def validate_template_coverage() -> dict:
    categories = set(d["category"] for d in LOCAL_KNOWLEDGE) | set(TEMPLATE_ALIASES.keys()) | {"unknown", "vague_problem", "photo_unclear", "sim_network_issue"}
    missing = {}
    for lang in LABELS:
        miss = []
        for cat in categories:
            if not get_template_content(lang, cat):
                miss.append(cat)
        if miss:
            missing[lang] = sorted(miss)
    return {"ok": not missing, "missing": missing, "languages": list(LABELS.keys()), "category_count": len(categories)}

rebuild_repairwise_indexes()
print(f"✅ {REPAIRWISE_VERSION} loaded")
print("Knowledge docs:", len(LOCAL_KNOWLEDGE))
print("Template coverage OK:", validate_template_coverage()["ok"])
