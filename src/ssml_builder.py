"""
SSML Builder — Converts plain text scripts to SSML markup for edge-tts.
Each channel has specific speaking rate, pitch, pause rules, and emphasis patterns.
"""
import re


# Per-channel SSML configuration
# V3: VO → VISUAL BREATHING → VO pattern (SYNCED with text overlay)
# Each VO segment plays during a TEXT scene, then a LONG pause fills a text-free scene
# sentence_break = pause between segments = should match 1 text-free scene duration (~4-6s)
SSML_CONFIG = {
    "yt_documenter": {
        "rate": "0.88",
        "pitch": "0%",
        "sentence_break": "4500ms",    # 4.5s = fills one text-free scene (doc pace: 5-9s/scene)
        "fact_break": "5500ms",        # 5.5s before major fact transition
        "section_break": "6000ms",     # 6s major section transition
        "emphasis_words": ["critically endangered", "vulnerable", "endangered",
                          "IUCN", "conservation", "species", "population"],
    },
    "yt_funny": {
        "rate": "1.05",
        "pitch": "+3%",
        "sentence_break": "3500ms",    # 3.5s comedic timing (fast channel: 1-3s/scene × ~2 scenes)
        "fact_break": "4000ms",        # 4s before punchline
        "section_break": "4500ms",     # 4.5s between jokes
        "emphasis_words": [],          # Comedy relies on timing not emphasis
    },
    "yt_anthro": {
        "rate": "0.92",
        "pitch": "+2%",
        "sentence_break": "4000ms",    # 4s contemplative pause (scene: 3-5s)
        "fact_break": "5000ms",        # 5s emotional beat
        "section_break": "5500ms",     # 5.5s scene change
        "emphasis_words": ["Gerald", "meanwhile", "however"],
    },
    "yt_pov": {
        "rate": "0.82",
        "pitch": "-5%",
        "sentence_break": "6000ms",    # 6s — LONG eerie silences (scene: 6-12s, tension needs space)
        "fact_break": "7000ms",        # 7s — uncomfortable pause
        "section_break": "8000ms",     # 8s — pure dread
        "emphasis_words": ["tonight", "someone", "something", "silence"],
    },
    "yt_drama": {
        "rate": "0.90",
        "pitch": "-3%",
        "sentence_break": "5000ms",    # 5s dramatic weight (scene: 2-12s variable)
        "fact_break": "6000ms",        # 6s emotional buildup
        "section_break": "7000ms",     # 7s dramatic transition
        "emphasis_words": ["Satu", "Dara", "Kecil", "THE SOUND", "quiet", "gone"],
    },
    "fb_fanspage": {
        "rate": "0.95",
        "pitch": "0%",
        "sentence_break": "3500ms",    # 3.5s quick but not rushed (scene: 3-6s)
        "fact_break": "4000ms",        # 4s between bold facts
        "section_break": "4500ms",     # 4.5s section change
        "emphasis_words": ["million", "billion", "percent", "endangered", "extinct"],
    },
}


def _clean_for_tts(text: str) -> str:
    """Remove characters that confuse TTS engines."""
    # Remove markdown-style formatting
    text = re.sub(r'[*_#\[\]()]', '', text)
    # Remove excessive punctuation
    text = re.sub(r'\.{2,}', '.', text)
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'\?{2,}', '?', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _add_emphasis(sentence: str, emphasis_words: list) -> str:
    """Add SSML emphasis tags around key words."""
    for word in emphasis_words:
        # Case-insensitive replacement with emphasis tags
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        sentence = pattern.sub(
            f'<emphasis level="moderate">{word}</emphasis>',
            sentence
        )
    return sentence


def _detect_numbers(sentence: str) -> str:
    """Add emphasis to numbers and statistics."""
    # Emphasize numbers with units (e.g., "180 degrees", "6 grams")
    sentence = re.sub(
        r'(\d+(?:\.\d+)?)\s*(degrees|grams|percent|million|billion|years|meters|centimeters|kilometers)',
        r'<emphasis level="strong">\1 \2</emphasis>',
        sentence,
        flags=re.IGNORECASE
    )
    return sentence


def build_ssml(script: str, account_key: str) -> str:
    """
    Converts a plain text script to SSML markup for edge-tts.
    
    Args:
        script: Plain text narration script
        account_key: Channel identifier (e.g., 'yt_documenter')
    
    Returns:
        SSML-formatted string ready for edge-tts
    """
    config = SSML_CONFIG.get(account_key, SSML_CONFIG["fb_fanspage"])
    
    # Clean the script
    cleaned = _clean_for_tts(script)
    
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', cleaned)
    
    ssml_parts = []
    
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
        
        # Add emphasis to keywords
        processed = _add_emphasis(sentence, config["emphasis_words"])
        
        # Add emphasis to numbers
        processed = _detect_numbers(processed)
        
        ssml_parts.append(f'    {processed}')
        
        # Determine break duration based on context
        if i < len(sentences) - 1:
            next_sentence = sentences[i + 1] if i + 1 < len(sentences) else ""
            
            # Longer break before section transitions (newlines in original)
            if sentence.endswith('.') and (
                next_sentence.startswith(('But', 'However', 'Meanwhile', 'Day', 'ACT', 'SCENE'))
                or any(w in sentence.lower() for w in ['endangered', 'extinct', 'population', 'iucn'])
            ):
                ssml_parts.append(f'    <break time="{config["fact_break"]}"/>')
            else:
                ssml_parts.append(f'    <break time="{config["sentence_break"]}"/>')
    
    # Wrap in SSML structure
    body = '\n'.join(ssml_parts)
    ssml = f"""<speak>
  <prosody rate="{config['rate']}" pitch="{config['pitch']}">
    <p>
{body}
    </p>
  </prosody>
</speak>"""
    
    return ssml


def get_edge_tts_params(account_key: str) -> dict:
    """
    Returns edge-tts voice parameters for the given account.
    These are used when SSML mode is not supported or as fallback.
    """
    voice_map = {
        "yt_documenter": {
            "voice": "en-US-AndrewNeural",
            "rate": "-12%",
            "pitch": "-5Hz",
        },
        "yt_funny": {
            "voice": "en-US-AnaNeural",
            "rate": "+5%",
            "pitch": "+3Hz",
        },
        "yt_anthro": {
            "voice": "en-US-BrianNeural",
            "rate": "-8%",
            "pitch": "+2Hz",
        },
        "yt_pov": {
            "voice": "en-US-MichelleNeural",
            "rate": "-18%",
            "pitch": "-5Hz",
        },
        "yt_drama": {
            "voice": "en-US-AndrewNeural",
            "rate": "-10%",
            "pitch": "-3Hz",
        },
        "fb_fanspage": {
            "voice": "en-US-EmmaNeural",
            "rate": "-5%",
            "pitch": "0Hz",
        },
    }
    return voice_map.get(account_key, voice_map["fb_fanspage"])
