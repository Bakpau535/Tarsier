"""
Fallback Script Bank — Pre-written tarsier scripts per channel persona.
V2: SHORT SEGMENT FORMAT per blueprint (4-5 short lines per script, ENGLISH).
Used when ALL Gemini/Groq API keys are exhausted.
RULE: Pipeline must NEVER fail due to API unavailability.

Each channel has 10+ unique scripts. The system picks based on topic hash
to ensure variety while being deterministic (same topic = same script).
"""

import hashlib
import random


# ========================================================
# YT_DOCUMENTER — Hook → Fact 1 → Fact 2 → Fact 3
# ========================================================
DOCUMENTER_SCRIPTS = [
    "Did you know a tarsier's eyes are as big as its brain?\nThis tiny primate hunts only in the darkness of night\nIts eyes can't move at all but its head rotates 180 degrees\nThe IUCN reports tarsier populations are declining every year",

    "Did you know tarsiers can leap 40 times their body length?\nTheir hind legs have tarsal bones that work like springs\nIn total darkness they hunt using hearing alone\nThe Philippine tarsier population is estimated at just 5,000 to 10,000",

    "Did you know tarsiers communicate using ultrasonic sound?\nTheir calls can reach 91 kilohertz, far beyond human hearing\nThis lets them talk without alerting any predators\nScientists only discovered this ability in 2012",

    "Did you know the tarsier is the only fully carnivorous primate?\nIt eats nothing but insects, small lizards, and even birds\nA single tarsier can eat 10 percent of its body weight each night\nThe Siau Island Tarsier is now classified as Critically Endangered",

    "Did you know tarsiers have existed for 55 million years?\nFossils show their anatomy has barely changed since then\nAncestral tarsiers once lived across America and Europe\nToday they survive only on the islands of Southeast Asia",

    "Did you know a baby tarsier weighs 25 percent of its mother?\nIn human terms that would be like giving birth to a 35-pound baby\nNewborns can grip branches from the moment they are born\nMothers can only produce one baby every six months",

    "Did you know tarsiers can die from stress alone?\nLoud noises can trigger fatal cardiac arrest in these animals\nThat is why tarsier sanctuaries in Bohol enforce strict silence rules\nCapturing tarsiers for the pet trade is illegal in the Philippines",

    "Did you know each tarsier eye weighs as much as its brain?\nAt 16 millimeters wide each eye is locked permanently in the skull\nTo look behind it must rotate its entire head around\nIts retina has one of the highest rod cell densities of any mammal",

    "Did you know tarsiers have the longest fingers relative to body size?\nTheir third finger is as long as their entire forearm\nThese fingers are perfect for gripping thin branches in darkness\nTarsiers spend almost their entire lives in the trees above",

    "Did you know the tarsier is the world's smallest primate?\nIt weighs just 85 to 160 grams, lighter than a smartphone\nYet it is one of the most efficient nocturnal hunters alive\nDeforestation and illegal trade are their biggest threats today",
]


# ========================================================
# YT_FUNNY — Setup → Scene → Expectation → Punchline
# ========================================================
FUNNY_SCRIPTS = [
    "Just gonna rest my eyes for 5 minutes\nThree hours later and I'm still wide awake\nTomorrow I'll definitely start being productive\nNarrator: tomorrow he said the exact same thing",

    "I said just 5 more minutes of this show\nOne more episode before bed I promise\nWoke up late for work again the next morning\nBoss: this is the third time this week",

    "Starting my diet on Monday for real this time\nBy Monday lunch I already ordered a burger\nIt's just one cheat meal it doesn't count\nNarrator: this was the 47th consecutive Monday",

    "Paycheck just hit my account this morning\nAfternoon I was just browsing online casually\nBy evening my balance was basically zero\nMy bank app: are you sure you want to continue?",

    "Told my friends I'm doing totally fine\nMeanwhile I've been overthinking since 11 PM\nCreating worst case scenarios that will never happen\nMy brain needs a premium subscription to turn this off",

    "You know that feeling when you wake up energized?\nYeah me neither\nSeven alarms and I can still ignore every single one\nThis pillow has its own gravitational field",

    "Planned to start my assignment at 8 AM sharp\n8 AM opened laptop and 9 AM opened YouTube\nNoon panic set in with 2 hours until deadline\nResult: 3 pages written in exactly 30 minutes",

    "My friend said my resting face looks terrifying\nBut I was actually in a great mood\nThis is just my default expression okay\nTarsier: finally someone who understands me",

    "Set my alarm for 5 AM to go running\n5 AM turned off alarm and went back to sleep\n10 AM woke up feeling guilty about not running\nTomorrow will be different... said me every single day",

    "Bought a brand new planner to get organized\nFirst week I wrote detailed plans every day\nSecond week the planner became a coffee coaster\nBest investment: collecting dust on my shelf",
]


# ========================================================
# YT_ANTHRO — Problem → Scene → Complaint → Resolution
# ========================================================
ANTHRO_SCRIPTS = [
    "Today was exhausting beyond words...\nWorking overtime every day but the paycheck stays the same\nSometimes I just want to quit everything\nBut here I am, setting my alarm for tomorrow morning",

    "Tired of pretending to be strong all the time...\nEveryone thinks I'm perfectly fine\nBut inside I'm falling apart piece by piece\nWho would even want to listen anyway?",

    "Working hard but nobody even notices...\nThe one who got promoted just talks the loudest\nI want to scream but the words won't come out\nGuess this is just how life works",

    "I just want some time for myself...\nFrom morning to night taking care of everyone else\nWhen I need someone, everyone disappears\nMaybe I need to learn to be selfish sometimes",

    "Sometimes I feel like I'm never enough...\nNo matter what I do it always feels like less\nTired of chasing standards I didn't even set\nMaybe enough isn't about achievements at all",

    "Everyone seems to know their purpose in life...\nI'm still figuring out what I even want\nGetting older but the direction is still unclear\nGuess I'll just keep walking and hope I find it",

    "Want to talk but scared of being a burden...\nSo I keep it all inside until it suffocates\nSmiling outside, chaos on the inside\nWhen can I be honest without being judged?",

    "Failed again today despite giving everything...\nTried my absolute hardest and it still wasn't enough\nIt feels like running on a treadmill going nowhere\nBut at least I'm still running, haven't stopped yet",

    "Missing home but I have to stay here...\nFar from family just trying to make a living\nSome nights feel longer than they should\nHope all of this means something someday",

    "Body is tired but my mind is even more tired...\nSleep doesn't come easy anymore\nWaking up in the morning feels impossibly heavy\nBut life keeps moving whether I want it to or not",
]


# ========================================================
# YT_POV — Normal → Scene → Tension → Reveal
# ========================================================
POV_SCRIPTS = [
    "You're alone in the forest at midnight\nSuddenly there's a strange sound right above your head\nDon't move... something is watching you\nTwo massive eyes stare at you from the darkness — a tarsier.",

    "The night feels wrong, the forest is too quiet\nUsually there are crickets but now there's only silence\nYou turn around and something moves in the branches\nA pair of giant eyes floating in the dark — just a tiny tarsier",

    "You wake up in your tent at 2 AM\nThere's a small shadow moving outside the fabric\nA soft scratching sound runs along the tent wall\nYou unzip it... a tiny tarsier face stares back at you",

    "You're walking through the Bohol forest alone at night\nThe trees are swaying but there's absolutely no wind\nSomething leaps from branch to branch right above you\nA night hunter smaller than your hand — the tarsier",

    "You hear a sound but can't figure out where it's coming from\nThe frequency is strange, not like any normal sound\nTurns out it's beyond the range of human hearing\nTarsiers communicate in ultrasonic waves you can't even detect",

    "You find tiny tracks pressed into the moss of an old tree\nLong finger marks with an impossibly strong grip pattern\nBelow it are the remains of an insect's exoskeleton\nThe world's smallest predator just had its dinner right here",

    "You set up an infrared camera in the forest tonight\nAt 3 AM there's a flash of movement across the screen\nSomething jumps 6 feet through pitch black air\nA tarsier catches a moth mid-flight without making a sound",

    "You sit perfectly still beneath a tree in total darkness\nSomething descends slowly down the trunk beside you\nIts head rotates 180 degrees and stares directly at you\nA tarsier — its eyes reflecting moonlight straight into yours",

    "You're night hiking and your flashlight suddenly dies\nThe forest goes pitch black in an instant\nA tiny sound comes from right next to your ear\nA small tarsier sits on a branch at exactly your head height",

    "You enter a small cave in Sulawesi in the late afternoon\nOn the ceiling there are dozens of tiny points of light\nNot fireflies, not crystals, not reflections\nTarsier eyes reflecting your flashlight as they sleep through the day",
]


# ========================================================
# YT_DRAMA — Opening → Scene → Conflict → Emotion → Closing
# ========================================================
DRAMA_SCRIPTS = [
    "She has lived alone since her mother left\nEvery night she waits on the same branch\nThe forest grows smaller, the sound of machines grows closer\nBut she stays, because there is nowhere else to go\nShe is just a tiny tarsier trying to survive",

    "This forest used to be vast and safe\nNow the trees fall one by one around her\nShe doesn't understand why her home is disappearing\nAll she knows is tonight feels colder than before\nTomorrow even this branch might be gone",

    "She gave birth during the heaviest monsoon rains\nHer baby was tiny but gripped her fur immediately\nThat first night the mother did not sleep, only watched\nThe world outside doesn't care about creatures this small\nBut a mother's love doesn't need anyone's permission",

    "He is the oldest one left in his group\nOne by one the others left and never came back\nNow it's just him and the silence between the trees\nStill hunting, still surviving, still completely alone\nBut his eyes aren't as sharp as they used to be",

    "That night he heard a sound he had never known before\nNot a predator, not wind, not rain falling\nA bright light cut through the darkness of his forest\nHe leaped to the highest branch he could reach\nBut the light kept getting closer",

    "They had been together for two full seasons\nCalling to each other at frequencies only they could hear\nUntil one night the call was not returned\nHe called again and again until the morning came\nThe forest answered him with nothing but silence",

    "Her baby fell from a branch while learning to leap\nTwo meters felt like a cliff for a body that small\nThe mother dove down as fast as physics allowed\nIn the wild there is no room for a second chance\nBut tonight, failure didn't mean the end",

    "His territory was taken by a younger, stronger male\nHe didn't fight back, his body isn't what it was\nHe moved to the edge of the forest to find new branches\nIn the new place no one recognizes him at all\nBut tarsiers don't know the meaning of giving up",

    "The rain hasn't stopped for three straight days\nThe insects are hiding and his stomach is empty\nHe sits curled inside a hollow in an ancient tree\nThe cold reaches deep into his fragile bones\nTomorrow he must hunt, no matter what happens",

    "They captured him during the day while he was sleeping\nLarge hands reached for his tiny body\nHe didn't fight back, just froze with his eyes wide open\nHis heart beat far too fast for something so small\nSome tarsiers never come back from human hands",
]


# ========================================================
# FB_FANSPAGE — Hook → Fact 1 → Fact 2 → CTA
# ========================================================
FB_SCRIPTS = [
    "This animal's eyes are heavier than its own brain!\nThe tarsier has the largest eyes relative to body size of any mammal\nIt can rotate its head nearly 360 degrees to hunt in total darkness\nShare this with a friend who doesn't know about this creature!",

    "This primate weighs less than your phone!\nThe tarsier weighs just 85 to 160 grams but can jump 40 times its length\nIt's the only primate on Earth that is 100% carnivorous\nTag a friend who's scared of tiny animals!",

    "This animal can talk but humans can't hear it!\nTarsiers communicate using ultrasonic sound up to 91 kilohertz\nThis is how they chat without predators knowing\nFollow for more incredible animal facts!",

    "A tarsier can die if you shout near it!\nExtreme stress can cause cardiac arrest in these tiny primates\nThat's why sanctuaries in Bohol enforce strict whisper-only rules\nShare this so more people know about tarsier conservation!",

    "This animal the size of your fist is 55 million years old!\nOlder than most mammals alive on the planet today\nFossils show its body has barely changed in all that time\nLike and share if you just learned this fact!",

    "Baby tarsiers are born at 25% of their mother's weight!\nIn human terms that's like giving birth to a 35-pound baby\nNewborns can grip branches from their very first minute alive\nShare this incredible animal fact with your friends!",

    "The tarsier has the sharpest night vision of any primate!\nIts retina is packed with specialized rod cells for minimal light\nIt can hunt in darkness levels as low as 0.001 lux\nFollow for amazing animal facts every day!",

    "The tarsier is the most efficient predator for its size!\nIn a single night it eats 10% of its entire body weight\nIt catches prey mid-air without making any sound at all\nTag a friend who loves learning about unique animals!",
]


# ========================================================
# MAIN LOOKUP
# ========================================================
FALLBACK_SCRIPTS = {
    "yt_documenter": DOCUMENTER_SCRIPTS,
    "yt_funny": FUNNY_SCRIPTS,
    "yt_anthro": ANTHRO_SCRIPTS,
    "yt_pov": POV_SCRIPTS,
    "yt_drama": DRAMA_SCRIPTS,
    "fb_fanspage": FB_SCRIPTS,
}


import os as _os
import json as _json
from datetime import datetime as _datetime

_DATA_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "data")
_USED_FB_IDX_FILE = _os.path.join(_DATA_DIR, "used_fallback_idx.json")

def _load_used_fb_indices() -> dict:
    try:
        with open(_USED_FB_IDX_FILE, "r") as f:
            return _json.load(f)
    except (FileNotFoundError, _json.JSONDecodeError):
        return {}

def _save_used_fb_indices(data: dict):
    _os.makedirs(_DATA_DIR, exist_ok=True)
    with open(_USED_FB_IDX_FILE, "w") as f:
        _json.dump(data, f, indent=2)

def get_fallback_script(account_key: str, topic: str, force_mashup: bool = False) -> tuple:
    """
    Get a unique fallback script based on channel + topic + date.
    Returns: (script_text, template_id) where template_id is stable for dedup.
    
    DEDUP STRATEGY:
    1. If unused templates exist → pick one, mark as used, return stable template_id
    2. If ALL templates exhausted OR force_mashup=True → create MASHUP from 2 templates
       Mashup = lines from template A + lines from template B
       This creates genuinely new, unique scripts that never repeat
    """
    import re
    scripts = FALLBACK_SCRIPTS.get(account_key, FB_SCRIPTS)
    
    # Use date + topic + account as seed — each call picks differently
    today = _datetime.now().strftime("%Y-%m-%d-%H-%M")
    combined = f"{account_key}::{topic}::{today}"
    topic_hash = int(hashlib.md5(combined.encode()).hexdigest(), 16)
    index = topic_hash % len(scripts)
    
    # If force_mashup, skip template lookup — go straight to mashup
    if force_mashup:
        attempts = len(scripts)  # Force exhaustion path
    else:
        # Persistent tracking: load previously used indices for this channel
        all_used = _load_used_fb_indices()
        used_set = set(all_used.get(account_key, []))
        
        # Try to find an unused template
        attempts = 0
        while index in used_set and attempts < len(scripts):
            index = (index + 1) % len(scripts)
            attempts += 1
    
    if attempts < len(scripts):
        # ========================================
        # NORMAL: unused template available
        # ========================================
        used_set.add(index)
        all_used[account_key] = list(used_set)
        _save_used_fb_indices(all_used)
        
        template_id = f"fb_{account_key}_{index}"
        script = scripts[index]
        
        print(f"[{account_key}] FALLBACK SCRIPT (template #{index+1}/{len(scripts)}) — "
              f"({len(script)} chars)")
        return script, template_id
    
    else:
        # ========================================
        # ALL TEMPLATES EXHAUSTED → CREATE MASHUP
        # Combine lines from 2 different templates
        # to create a genuinely new, unique script
        # ========================================
        print(f"[{account_key}] All {len(scripts)} templates exhausted — creating MASHUP script")
        
        # Pick 2 different templates using hash
        idx_a = topic_hash % len(scripts)
        idx_b = (topic_hash // len(scripts) + 1) % len(scripts)
        if idx_b == idx_a:
            idx_b = (idx_a + 1) % len(scripts)
        
        script_a = scripts[idx_a]
        script_b = scripts[idx_b]
        
        # Split both into lines (new format: newline-separated segments)
        lines_a = [l.strip() for l in script_a.split('\n') if l.strip()]
        lines_b = [l.strip() for l in script_b.split('\n') if l.strip()]
        
        # Mashup: take first line from A, middle lines alternating, last from B
        mashup_lines = []
        if lines_a:
            mashup_lines.append(lines_a[0])  # Hook/Setup from A
        
        # Middle lines: alternate between A and B
        max_middle = max(len(lines_a) - 2, len(lines_b) - 2)
        for i in range(max_middle):
            if i % 2 == 0 and i + 1 < len(lines_b) - 1:
                mashup_lines.append(lines_b[i + 1])
            elif i + 1 < len(lines_a) - 1:
                mashup_lines.append(lines_a[i + 1])
        
        if lines_b:
            mashup_lines.append(lines_b[-1])  # Closing from B
        
        # Ensure we have 4-5 lines
        mashup_lines = mashup_lines[:5]
        if len(mashup_lines) < 3:
            mashup_lines = lines_a  # Safety fallback
        
        script = '\n'.join(mashup_lines)
        
        # Unique template_id using pair + timestamp (never same)
        ts = int(_datetime.now().timestamp())
        template_id = f"fb_{account_key}_mashup_{idx_a}_{idx_b}_{ts}"
        
        print(f"[{account_key}] MASHUP SCRIPT (mix #{idx_a+1}+#{idx_b+1}) — "
              f"({len(script)} chars, {len(mashup_lines)} lines)")
        return script, template_id
