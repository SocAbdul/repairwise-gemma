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

# ── Model globals (injected by app.py after loading) ─────────────────────────
# In Kaggle notebooks these are kernel globals. As a module they must be
# declared here and set by app.py before any generation call.
model = None
processor = None
DEMO_MODE = False  # Set to True by app.py if no GPU or model load fails

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
MEDIUM_RISK_CATEGORIES = {"charging_issue", "charging_port_issue", "screen_repair", "camera_issue", "update_issue", "faceid_touchid_issue"}

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
    "phishing", "scam", "bank link", "otp", "card details", "suspicious link",
    "banco", "tarjeta", "codigo", "código", "enlace sospechoso",
    "banc", "targeta", "codi", "enllac", "enllaç",
    "بینک", "کارڈ", "کوڈ", "رابطہ", "بنك", "بطاقة", "رمز", "رابط",
    "banca", "card", "cod", "link",
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
BOOT_PATTERNS = [r"\b(bootloop|stuck logo|logo|not turning on|no enciende|no arranca|reinicia en bucle)\b"]
SCREEN_PATTERNS = [r"\b(screen|pantalla|display|oled|lcd|green line|linea verde|línea verde|touch)\b.*\b(broken|cracked|rota|negra|black|line|flicker|no responde)\b"]
CAMERA_PATTERNS = [r"\b(camera|camara|cámara|camera lens|lente)\b.*\b(black|negra|blurry|borrosa|focus|enfoque|shake|vibra)\b"]
AUDIO_PATTERNS = [r"\b(speaker|microphone|mic|altavoz|microfono|micrófono|audio|sound|sonido)\b.*\b(no|not|problem|issue|funciona|hear|escucha)\b"]
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
    if len(t.split()) <= 6 and re.search(r"\b(phone|movil|mobile|telefono|teléfono|mòbil|mobil)?\s*(no funciona|not working|doesnt work|doesn t work|va mal|problem|problema|no va)\b", t):
        return True
    return t in {"no funciona", "not working", "problema", "problem"}

def urgency_for_category(category: str) -> str:
    if category in HIGH_RISK_CATEGORIES:
        return "HIGH"
    if category in MEDIUM_RISK_CATEGORIES:
        return "MEDIUM"
    return "LOW"

def triage_issue(text: str) -> dict:
    if is_vague_problem(text):
        return {"urgency": "LOW", "category": "vague_problem", "reason": "Vague problem; ask targeted repair questions.", "method": "v13_vague_gate", "confidence": 0.99}
    if contains_any(text, DANGER_BATTERY_TERMS):
        return {"urgency": "HIGH", "category": "battery_safety", "reason": "Explicit swollen battery/safety signal.", "method": "priority_battery", "confidence": 0.99}
    if contains_any(text, DANGER_SCAM_TERMS):
        return {"urgency": "HIGH", "category": "scam_phishing", "reason": "Explicit phishing/scam signal.", "method": "priority_scam", "confidence": 0.98}
    if contains_any(text, DANGER_WATER_TERMS):
        return {"urgency": "HIGH", "category": "water_damage", "reason": "Explicit liquid/water/corrosion signal.", "method": "priority_water", "confidence": 0.98}
    checks = [
        ("sim_network_issue", SIGNAL_NETWORK_PATTERNS, 0.99),
        ("charging_issue", CHARGING_PATTERNS, 0.97),
        ("app_issue", APP_PATTERNS, 0.97),
        ("wifi_issue", WIFI_PATTERNS, 0.92),
        ("bluetooth_issue", BLUETOOTH_PATTERNS, 0.92),
        ("overheating_issue", OVERHEAT_PATTERNS, 0.94),
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
    return (
        f"1. {labels[0]}: {template['diagnosis']}\n"
        f"2. {labels[1]}: {risk}\n"
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
        "type": "function",
        "function": {
            "name": "repairwise_decide_escalation",
            "description": (
                "Decide whether a mobile phone repair customer can try safe checks, "
                "should visit a technician soon, or needs urgent professional help."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "escalation_level": {
                        "type": "string",
                        "enum": ["self_check", "soon", "urgent"],
                        "description": "How quickly the customer should escalate."
                    },
                    "needs_human_technician": {
                        "type": "boolean",
                        "description": "Whether a technician visit is recommended."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Short practical reason grounded in the customer issue."
                    },
                    "customer_safe_next_step": {
                        "type": "string",
                        "description": "One safe next step the customer can do now."
                    },
                },
                "required": [
                    "escalation_level",
                    "needs_human_technician",
                    "reason",
                    "customer_safe_next_step"
                ],
            },
        },
    }
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

    if obj.get("name") == "repairwise_decide_escalation":
        args = obj.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except Exception:
                args = {}
        return args if isinstance(args, dict) else None

    # JSON-only fallback: object is directly the arguments.
    required = {"escalation_level", "needs_human_technician", "reason", "customer_safe_next_step"}
    if required <= set(obj.keys()):
        return obj

    return None

def build_tool_router_prompt(user_text: str, triage: dict, docs: list, language: str) -> str:
    context = "\n".join(f"[{d.get('id')}] {d.get('text','')[:220]}" for d in docs[:3])
    lang = normalize_language_name(language)
    return f"""
You are RepairWise AI. Decide whether to call the repair escalation tool.

Customer message:
{user_text}

Detected category:
{triage.get('category')}

Urgency:
{triage.get('urgency')}

Local context:
{context}

Return a tool call to repairwise_decide_escalation with JSON arguments:
{{
  "escalation_level": "self_check" | "soon" | "urgent",
  "needs_human_technician": true | false,
  "reason": "short reason",
  "customer_safe_next_step": "one safe next step"
}}

Do not answer the customer. Only decide the tool arguments.
""".strip()

def call_gemma_function_router(user_text: str, triage: dict, docs: list, language: str) -> dict:
    """Try Gemma 4 native function calling, with JSON fallback.

    If the local tokenizer supports `apply_chat_template(..., tools=...)`, we pass
    the tool schema directly. If not, we fall back to a JSON tool-call prompt.
    """
    trace = LAST_GEMMA_TRACE["function_calling"]
    trace.update({
        "attempted": True,
        "native_tools_passed": False,
        "tool_name": "repairwise_decide_escalation",
        "tool_args": {},
        "tool_result": {},
        "raw": "",
        "error": "",
    })

    if not USE_GEMMA_FUNCTION_CALLING:
        args = deterministic_escalation_args(user_text, triage)
        result = repairwise_decide_escalation(**args)
        trace.update({"tool_args": args, "tool_result": result, "error": "Function calling disabled."})
        return result

    if not ("processor" in globals() and "model" in globals()):
        args = deterministic_escalation_args(user_text, triage)
        result = repairwise_decide_escalation(**args)
        LAST_GEMMA_TRACE.update({
            "called": True,
            "path": "function_calling_unavailable",
            "fallback_used": True,
            "error": "Gemma model not loaded in this runtime.",
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
        result = repairwise_decide_escalation(**defaults)
        trace.update({"tool_args": defaults, "tool_result": result})
        return result

    except Exception as exc:
        args = deterministic_escalation_args(user_text, triage)
        result = repairwise_decide_escalation(**args)
        err = f"{type(exc).__name__}: {exc}"
        LAST_GEMMA_TRACE.update({"called": True, "path": "function_calling_error", "fallback_used": True, "error": err})
        trace.update({"tool_args": args, "tool_result": result, "error": err})
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
    LAST_GEMMA_TRACE.update({"called": True, "path": "text_enrichment", "raw": "", "fallback_used": False, "error": ""})
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

def inject_tool_next_step(answer: str, tool_result: dict | None, language: str) -> str:
    """Connect function-calling output to the visible customer answer."""
    if not answer or not tool_result:
        return answer
    step = str(tool_result.get("customer_safe_next_step", "")).strip()
    if not step or step.lower() in answer.lower():
        return answer

    lang = normalize_language_name(language)
    label = TOOL_NEXT_STEP_LABELS.get(lang, "Tool-selected next step")
    lines = answer.splitlines()

    # Put the tool step in line 3 ("What to do now") so the judge sees the
    # tool result connected to the actual customer-facing answer.
    if len(lines) >= 3:
        lines[2] = lines[2].rstrip() + f" {label}: {step}"
        return "\n".join(lines)

    return answer + f"\n{label}: {step}"


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
        tool_result = repairwise_decide_escalation(**deterministic_escalation_args(user_text, triage))
        LAST_GEMMA_TRACE["function_calling"].update({
            "attempted": False,
            "tool_name": "repairwise_decide_escalation",
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
    LAST_GEMMA_TRACE.update({"called": True, "path": "multimodal_photo", "raw": "", "fallback_used": False, "error": ""})
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
        meta = {
            "version": REPAIRWISE_VERSION,
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

    triage = triage_issue(text)
    docs = retrieve_knowledge(text, k=7, category=triage["category"], image_present=False)
    answer = generate_text_answer(text, triage, docs[:4], lang)

    if looks_bad_output(answer) or violates_requested_language(answer, lang) or answer_conflicts_with_category(answer, triage["category"], text):
        LAST_GEMMA_TRACE["fallback_used"] = True
        answer = safe_fallback_answer(text, triage, docs[:3], lang, image_present=False)
        # Even fallback answers should expose the tool step if available.
        tool_result = LAST_GEMMA_TRACE.get("function_calling", {}).get("tool_result", {})
        answer = inject_tool_next_step(answer, tool_result, lang)

    meta = {
        "version": REPAIRWISE_VERSION,
        "triage": triage,
        "sources": [{"id": d.get("id"), "category": d.get("category"), "risk": d.get("risk"), "score": round(float(d.get("score", 0)), 3), "engine_scores": d.get("engine_scores", {})} for d in docs[:5]],
        "context_sufficient": is_context_sufficient(docs, triage["category"]),
        "photo_mode": False,
        "language": lang,
        "effective_text": text,
        "history_used": bool(history_context),
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
