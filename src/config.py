import os
from dotenv import load_dotenv

# Load environment variables from .env file for local development
load_dotenv()

# --- API Keys ---
# Gemini 2.5 Flash — 12 key rotasi untuk kapasitas maksimal
_gemini_keys_raw = [
    os.environ.get("GEMINI_API_KEY_1", ""),
    os.environ.get("GEMINI_API_KEY_2", ""),
    os.environ.get("GEMINI_API_KEY_3", ""),
    os.environ.get("GEMINI_API_KEY_4", ""),
    os.environ.get("GEMINI_API_KEY_5", ""),
    os.environ.get("GEMINI_API_KEY_6", ""),
    os.environ.get("GEMINI_API_KEY_7", ""),
    os.environ.get("GEMINI_API_KEY_8", ""),
    os.environ.get("GEMINI_API_KEY_9", ""),
    os.environ.get("GEMINI_API_KEY_10", ""),
    os.environ.get("GEMINI_API_KEY_11", ""),
    os.environ.get("GEMINI_API_KEY_12", ""),
]
GEMINI_API_KEYS = [k for k in _gemini_keys_raw if k]
GEMINI_API_KEY = GEMINI_API_KEYS[0] if GEMINI_API_KEYS else ""

# DIAGNOSTIC: Print key prefixes to verify secrets are loaded correctly
print(f"[Config] Gemini keys loaded: {len(GEMINI_API_KEYS)} active")
for i, k in enumerate(_gemini_keys_raw):
    label = f"KEY_{i+1}"
    prefix = k[:8] + "..." if k else "*** EMPTY ***"
    print(f"  {label}: {prefix}")

# Per-channel Gemini key assignment — each channel gets 2 dedicated keys
# to prevent one channel from exhausting another's quota
GEMINI_KEY_MAP = {
    "yt_documenter": os.environ.get("GEMINI_API_KEY_1", ""),
    "yt_funny":      os.environ.get("GEMINI_API_KEY_2", ""),
    "yt_anthro":     os.environ.get("GEMINI_API_KEY_3", ""),
    "yt_pov":        os.environ.get("GEMINI_API_KEY_4", ""),
    "yt_drama":      os.environ.get("GEMINI_API_KEY_5", ""),
    "fb_fanspage":   os.environ.get("GEMINI_API_KEY_6", ""),
}
# Backup Gemini keys — one extra key per channel
GEMINI_KEY_MAP_BACKUP = {
    "yt_documenter": os.environ.get("GEMINI_API_KEY_7", ""),
    "yt_funny":      os.environ.get("GEMINI_API_KEY_8", ""),
    "yt_anthro":     os.environ.get("GEMINI_API_KEY_9", ""),
    "yt_pov":        os.environ.get("GEMINI_API_KEY_10", ""),
    "yt_drama":      os.environ.get("GEMINI_API_KEY_11", ""),
    "fb_fanspage":   os.environ.get("GEMINI_API_KEY_12", ""),
}

# Freesound API Key for background music
FREESOUND_API_KEY = os.environ.get("FREESOUND_API_KEY", "")
# 12 HF Inference API Keys — 2 per account (primary + backup)
HF_API_KEYS = {
    "yt_documenter": os.environ.get("HF_API_KEY_1", ""),
    "yt_funny": os.environ.get("HF_API_KEY_2", ""),
    "yt_anthro": os.environ.get("HF_API_KEY_3", ""),
    "yt_pov": os.environ.get("HF_API_KEY_4", ""),
    "yt_drama": os.environ.get("HF_API_KEY_5", ""),
    "fb_fanspage": os.environ.get("HF_API_KEY_6", "")
}
# Backup HF keys — one extra key per account
HF_API_KEYS_BACKUP = {
    "yt_documenter": os.environ.get("HF_API_KEY_7", ""),
    "yt_funny": os.environ.get("HF_API_KEY_8", ""),
    "yt_anthro": os.environ.get("HF_API_KEY_9", ""),
    "yt_pov": os.environ.get("HF_API_KEY_10", ""),
    "yt_drama": os.environ.get("HF_API_KEY_11", ""),
    "fb_fanspage": os.environ.get("HF_API_KEY_12", "")
}

# --- Account Configurations ---
ACCOUNTS = {
    "yt_documenter": {
        "platform": "YT",
        "name": "Tarsier Nusantara",
        "concept": "BBC/NatGeo Documentary",
        "description": "Scientific documentary channel. Authoritative, calm, data-driven narration like David Attenborough. Each video: hook + 3 facts + IUCN data + conservation CTA.",
        "bio": "Exploring the science behind Tarsiers — one of the world's smallest primates. Biology, habitat, conservation status, and research updates. 🔬🐒 #Tarsier #Wildlife #Conservation",
        "audience": "Nature documentary lovers, students, educators, wildlife researchers",
        "music_style": "Cinematic instrumental, 55-70 BPM",
        "tone": "Authoritative, scientific, formal — like a BBC documentary narrator",
        "color_theme": ["#1B2838", "#2196F3", "#4CAF50"],
        "thumbnail_style": "Background gelap, font tegas, warna biru/hijau, kesan ilmiah",
        "flux_allowed": False,
    },
    "yt_funny": {
        "platform": "YT",
        "name": "Tarsier Funny",
        "concept": "Viral Wildlife Comedy",
        "description": "Meme-style comedy channel. Punchy captions, fast cuts, reaction shots, slow-mo replays. Every caption lands like a punchline.",
        "bio": "The funniest tarsier moments on the internet! Cute, hilarious, and guaranteed to make your day. 😂🐵 #FunnyAnimals #Tarsier #Cute",
        "audience": "Casual viewers, animal lovers, meme community, young audience",
        "music_style": "Upbeat comedy, 115-130 BPM",
        "tone": "Meme-literate, punchy, internet-native humor",
        "color_theme": ["#FF6B35", "#FFD166", "#06D6A0"],
        "thumbnail_style": "Warna cerah, font bulat lucu, ekspresi tarsier menggemaskan",
        "flux_allowed": False,
    },
    "yt_anthro": {
        "platform": "YT",
        "name": "Tarsier Humans",
        "concept": "Sitcom Sketch Comedy",
        "description": "Sketch comedy — tarsier living human life. Deadpan narrator, scene cards, escalation to punchline. Never acknowledge tarsier is an animal.",
        "bio": "What if tarsiers lived like humans? Daily life, drama, comedy — all from a tarsier's perspective! 🐒💼 #Anthropomorphic #Tarsier #Viral",
        "audience": "Animation fans, comedy lovers, viral content chasers, teens",
        "music_style": "Quirky jazz, light comedy, 85-100 BPM",
        "tone": "Deadpan conversational, sketch comedy writer",
        "color_theme": ["#E8871E", "#FFB84D", "#F5E6CC"],
        "thumbnail_style": "Tarsier dengan atribut manusia, warna warm",
        "flux_allowed": True,  # For human world backgrounds only
    },
    "yt_pov": {
        "platform": "YT",
        "name": "I Am Tarsier",
        "concept": "First-Person Diary (Kiko)",
        "description": "Serialized diary from tarsier Kiko's perspective. Intimate, poetic, sensory. Each entry = one night. Conservation through confusion, not lecture.",
        "bio": "See the world through my eyes. I'm a tarsier — and this is my story. 🌿👁️ #TarsierPOV #Conservation #Storytelling",
        "audience": "Storytelling fans, conservation-minded viewers, emotional content seekers",
        "music_style": "Ambient minimal, 45-60 BPM",
        "tone": "Intimate whisper, first-person diary, reflective and poetic",
        "color_theme": ["#2D3436", "#636E72", "#00B894"],
        "thumbnail_style": "Sudut pandang mata tarsier, tone sinematik",
        "flux_allowed": True,  # For atmospheric forest scenes only
    },
    "yt_drama": {
        "platform": "YT",
        "name": "Tarsier Tales",
        "concept": "Episodic Conservation Drama",
        "description": "Serialized drama with characters: Satu (protagonist), Dara (partner), Kecil (juvenile), THE SOUND (antagonist). Real conservation issues through character-driven storytelling.",
        "bio": "Dramatic stories of tarsier survival, loss, and hope. Each episode is a new chapter. 🎭🐒 #TarsierTales #WildlifeDrama #Series",
        "audience": "Series lovers, emotional content fans, conservation supporters",
        "music_style": "Orchestral cinematic, 65-90 BPM variable",
        "tone": "Dramatic narrator, emotional weight, tension builds across episodes",
        "color_theme": ["#2C3E50", "#E74C3C", "#F39C12"],
        "thumbnail_style": "Poster style, tone dramatis, warna kontras",
        "flux_allowed": True,  # For dramatic environment scenes only
    },
    "fb_fanspage": {
        "platform": "FB",
        "name": "Tarsier World",
        "concept": "Shareable Fact Aggregator",
        "description": "Bold facts, high contrast visuals, text on every shot. Must be watchable WITHOUT audio. Repurpose best clips from YT channels with new text overlay.",
        "bio": "🌍 Tarsier World — shocking facts, stunning footage, and why these tiny primates matter. Share if you care! 🐒🌿",
        "audience": "Facebook wildlife community, casual scrollers, sharers",
        "music_style": "Upbeat informational, 90-110 BPM",
        "tone": "Energetic, conversational, shareable hooks",
        "color_theme": ["#1B5E20", "#FF6F00", "#FFFFFF"],
        "thumbnail_style": "Bold text overlay, high contrast, attention-grabbing",
        "flux_allowed": False,
    }
}

# --- Per-Channel Video Production Profiles (from correction-plan-tarsier.md) ---
# This is the "Video DNA" — each channel builds its video differently.
VIDEO_PROFILES = {
    "yt_documenter": {
        "cut_duration": (5, 9),        # seconds per shot — slow, documentary pace
        "transition": "dissolve",       # dissolve 0.5s between shots
        "aspect_ratio": "16:9",
        "letterbox": False,
        "tarsier_min_pct": 75,          # tarsier on-screen minimum 75%
        "has_voiceover": True,
        "visual_source": "stock_only",  # Pexels + Pixabay real footage ONLY, ZERO FLUX
        "color_grade": "documentary",   # desaturate 20%, teal-green, shadow lift
        "loop_style": "standard",       # normal, slow-mo, ken burns, flip, crop-eyes
        "loop_habitat_interval": 4,     # insert habitat B-roll every 4 tarsier variations
        "text_overlay": "data_only",    # text only for scientific data/numbers
    },
    "yt_funny": {
        "cut_duration": (1, 3),         # fast energetic cuts
        "transition": "hard_cut",       # NO dissolve — punchy hard cuts
        "aspect_ratio": "16:9",
        "letterbox": False,
        "tarsier_min_pct": 85,          # tarsier dominant
        "has_voiceover": False,         # ZERO voiceover — captions + sound effects only
        "visual_source": "ai_only",      # 100% AI tarsier images for funny channel
        "color_grade": "comedy",        # saturasi +15%, warm orange, bright
        "loop_style": "replay",         # each moment: normal → slow-mo → zoom (3x replay)
        "loop_habitat_interval": 0,     # no habitat B-roll for funny
        "text_overlay": "meme_caption", # bold rounded font, colorful, meme-style
    },
    "yt_anthro": {
        "cut_duration": (3, 5),         # medium pace
        "transition": "dissolve",
        "aspect_ratio": "16:9",
        "letterbox": False,
        "tarsier_min_pct": 70,
        "has_voiceover": True,
        "visual_source": "stock_plus_flux_env",  # stock tarsier + FLUX human-world backgrounds
        "color_grade": "sitcom",        # warm tone, slight vignette
        "loop_style": "reaction",       # silent reaction loops (tarsier stares, 2-3x crop)
        "loop_habitat_interval": 0,
        "text_overlay": "subtitle",     # bold subtitle with semi-transparent black bg
    },
    "yt_pov": {
        "cut_duration": (6, 12),        # slowest — cinematic breathing room
        "transition": "dissolve",       # dissolve or fade ONLY, NO hard cuts
        "aspect_ratio": "16:9",
        "letterbox": False,
        "tarsier_min_pct": 80,
        "has_voiceover": True,
        "visual_source": "stock_plus_flux_env",  # stock tarsier + FLUX atmospheric forests
        "color_grade": "night_vision",  # blue shadows, yellow highlights, film grain +25%
        "loop_style": "drift",          # very slow float movement (1-2% pan over 8s)
        "loop_habitat_interval": 0,
        "text_overlay": "none",         # ZERO text except "Day [N]" title card
    },
    "yt_drama": {
        "cut_duration": (2, 12),        # variable — 2s action, 8-12s emotional moments
        "transition": "dissolve",
        "aspect_ratio": "16:9",
        "letterbox": True,              # black bars top+bottom for cinematic 2.35:1
        "tarsier_min_pct": 65,          # lowest — intentional environment scenes
        "has_voiceover": True,
        "visual_source": "stock_plus_flux_env",  # stock tarsier + FLUX dramatic scenes
        "color_grade": "drama",         # variable: warm green (safe), cold blue (danger)
        "loop_style": "emotional",      # very slow ken burns 2% over 10s
        "loop_habitat_interval": 0,
        "text_overlay": "title_card",   # episode title card, font serif dramatis
    },
    "fb_fanspage": {
        "cut_duration": (3, 6),
        "transition": "dissolve",
        "aspect_ratio": "1:1",          # SQUARE format for Facebook feed
        "letterbox": False,
        "tarsier_min_pct": 80,
        "has_voiceover": True,
        "visual_source": "stock_only",  # repurpose best clips, ZERO FLUX
        "color_grade": "vivid",         # vivid, high contrast, stand out in feed
        "loop_style": "standard",
        "loop_habitat_interval": 0,
        "text_overlay": "bold_overlay", # bold typography on EVERY shot
    },
}

# --- Pipeline Constants ---
MINIMUM_QC_SCORE = 80
MAX_RETRIES = 3
VIDEO_RESOLUTION = "1080p"
CLIP_DURATION_SEC = 6
SHORT_DURATIONS_SEC = (15, 30)

# --- YouTube OAuth2 Credentials (per akun) ---
# Mapping akun YT ke credential JSON dari .env
YT_OAUTH_CREDENTIALS = {
    "yt_documenter": os.environ.get("YT_1_JASON", ""),
    "yt_funny": os.environ.get("YT_2_JASON", ""),
    "yt_anthro": os.environ.get("YT_3_JASON", ""),
    "yt_pov": os.environ.get("YT_4_JASON", ""),
    "yt_drama": os.environ.get("YT_5_JASON", ""),
}

# --- GitHub Repository URL ---
GITHUB_URL = os.environ.get("GITHUB_URL", "")

# Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
TMP_DIR = os.path.join(BASE_DIR, "tmp")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
TOPICS_FILE = os.path.join(DATA_DIR, "topics.json")

# Ensure required directories exist
for d in [DATA_DIR, TMP_DIR, TEMPLATES_DIR]:
    os.makedirs(d, exist_ok=True)

# --- Prompts ---
# Script generation now uses persona briefs from persona_prompts.py
# This is the wrapper prompt that includes the channel's persona brief
SCRIPT_GENERATION_PROMPT = """
{persona_brief}

TOPIC/FACTS TO USE:
{topic}

IMPORTANT RULES:
- Write ENTIRELY IN ENGLISH
- Target: approximately 5-6 sentences (~45 seconds when spoken aloud at normal pace)
- CRITICAL: Keep the script SHORT — maximum 400 characters total. TTS with SSML reads very slowly (~8 chars/sec).
- Follow the STRUCTURE defined above EXACTLY
- Provide ONLY the narration script — no formatting labels, no scene directions, no markdown
- Every script must be UNIQUE — do not use generic templates
- CRITICAL: Focus exclusively on the MAIN TOPIC specified above
- Do NOT repeat generic tarsier overview facts — write ONLY about the specific topic
- Each script must contain facts and angles that are DIFFERENT from any previous script
- Include at least 3 facts that are SPECIFIC to the topic, not general tarsier information

VOCABULARY RULES:
- BANNED WORDS (never use): "equal", "equivalent", "roughly", "approximately", "incredible", "amazing", "fascinating"
- Never repeat the same adjective or comparison word twice in one script
- Use varied sentence structures — mix short and long sentences
- Avoid cliche phrases like "did you know", "in fact", "it turns out"
- Each script must sound naturally different from any other script
"""

METADATA_GENERATION_PROMPT = """
Based on the following narration script:
"{script}"

{title_formula}

Generate YouTube metadata with these requirements:
1. Title (SEO optimized, English, max 60 characters). Follow the title formula above.
2. Detailed video description in English. Minimum 100 words.
3. 5 relevant hashtags that are UNIQUE to this channel's style.
4. 10 keyword tags — at least 60% must be different from other channels covering the same topic.
5. Most relevant YouTube category (e.g. "Education", "Pets & Animals", "Science & Technology", or "Entertainment").
6. Language must be "en" (English).

DIFFERENTIATION RULES:
- Title must NOT share the same first 3 words with any other channel's title.
- Description must be unique to this channel's voice and style.

Output PURE JSON without markdown backticks:
{
  "title": "Title Here",
  "description": "Description here...",
  "hashtags": ["#tag1", "#tag2"],
  "tags": ["keyword1", "keyword2"],
  "category": "Education",
  "language": "en"
}
"""

