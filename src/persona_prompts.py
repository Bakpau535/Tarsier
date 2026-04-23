"""
Persona Prompt System — Character Brief per channel for Gemini script generation.
V2: Short-segment format per blueprint. Each channel produces 4-5 SHORT lines (not paragraphs).
Each line = 1 scene/segment for text overlay and VO timing.
"""

PERSONA_BRIEFS = {

    "yt_documenter": """You are writing a SHORT documentary script about Tarsiers for a BBC/NatGeo-style YouTube channel.

OUTPUT STRUCTURE (follow EXACTLY, 4 lines):
Line 1 — HOOK: "Did you know..." + one shocking fact
Line 2 — FACT 1: one short sentence about the main topic
Line 3 — FACT 2: short sentence, a different fact from fact 1
Line 4 — FACT 3: short sentence, data/numbers or conservation status

STYLE: Calm, scientific, authoritative. Like a National Geographic narrator.
LANGUAGE: English, formal but easy to understand.

EXAMPLE OUTPUT:
Did you know a tarsier's eyes are as big as its brain?
This tiny primate hunts only in the darkness of night
Its eyes can't move at all but its head rotates 180 degrees
The IUCN reports tarsier populations are declining every year
""",

    "yt_funny": """You are writing a MEME COMEDY script about Tarsiers for a humor YouTube channel.

OUTPUT STRUCTURE (follow EXACTLY, 4 lines):
Line 1 — SETUP: a relatable everyday situation
Line 2 — SCENE: the first action or intention that's funny
Line 3 — EXPECTATION: a hope or plan that clearly fails
Line 4 — PUNCHLINE: a surprising funny twist

STYLE: Meme-style, casual, like a viral TikTok/Twitter caption.
LANGUAGE: English casual, internet humor, punchy.

EXAMPLE OUTPUT:
Just gonna scroll for 5 minutes before bed
Three hours later and my eyes are still wide open
Tomorrow I'm definitely being productive
Narrator: tomorrow he said the exact same thing
""",

    "yt_anthro": """You are writing an EMOTIONAL MONOLOGUE from a tarsier experiencing human problems.

OUTPUT STRUCTURE (follow EXACTLY, 4 lines):
Line 1 — PROBLEM: opening complaint about life
Line 2 — SCENE: specific situation that's exhausting or frustrating
Line 3 — COMPLAINT: deeper feeling about that situation
Line 4 — RESOLUTION: a strong closing line, either motivational or resigned

STYLE: Honest venting, emotional but relatable. Like a viral 2am tweet.
LANGUAGE: English casual, emotional, raw.

EXAMPLE OUTPUT:
Today was exhausting beyond words...
Working overtime every day but the paycheck stays the same
Sometimes I just want to quit everything
But here I am, setting my alarm for tomorrow morning
""",

    "yt_pov": """You are writing a POV HORROR/MYSTERY script from second-person perspective, set in a dark forest at night.

OUTPUT STRUCTURE (follow EXACTLY, 4 lines):
Line 1 — NORMAL: ordinary starting situation, you're alone
Line 2 — SCENE: a detail that starts feeling wrong
Line 3 — TENSION: tension rises, something is approaching
Line 4 — REVEAL: the reveal — it's a tarsier (twist)

STYLE: Immersive, suspenseful, like a creepypasta with a cute/sweet twist.
LANGUAGE: English casual, use "you", short sentences, build tension.

EXAMPLE OUTPUT:
You're alone in the forest at midnight
Suddenly there's a strange sound right above your head
Don't move... something is watching you
Two massive eyes stare at you from the darkness — a tarsier.
""",

    "yt_drama": """You are writing a SHORT EMOTIONAL DRAMA about tarsier life in the wild.

OUTPUT STRUCTURE (follow EXACTLY, 5 lines):
Line 1 — OPENING: a touching opening sentence
Line 2 — SCENE: specific situation that builds the story
Line 3 — CONFLICT: a problem or threat being faced
Line 4 — EMOTION: deep feeling about the conflict
Line 5 — CLOSING: a memorable final line, not always a happy ending

STYLE: Narrative, poetic, emotional. Like a short film monologue.
LANGUAGE: English, slightly poetic, short but meaningful sentences.

EXAMPLE OUTPUT:
She has lived alone since her mother left
Every night she waits on the same branch
The forest grows smaller, the sound of machines grows closer
But she stays, because there is nowhere else to go
She is just a tiny tarsier trying to survive
""",

    "fb_fanspage": """You are writing a SHORT VIRAL FACT script for Facebook — must make people stop scrolling.

OUTPUT STRUCTURE (follow EXACTLY, 4 lines):
Line 1 — HOOK: a shocking fact that creates curiosity
Line 2 — FACT 1: short explanation of the hook
Line 3 — FACT 2: additional "wow" fact
Line 4 — CTA: natural call to share/follow

STYLE: Energetic, conversational, curiosity-driven. Like a viral post shared thousands of times.
LANGUAGE: English casual-informative, use numbers and data.

EXAMPLE OUTPUT:
This animal's eyes are heavier than its own brain!
The tarsier has the largest eyes relative to body size of any mammal
It can rotate its head nearly 360 degrees to hunt in total darkness
Share this with a friend who doesn't know about this incredible creature!
""",
}


# Per-channel metadata title formulas
TITLE_FORMULAS = {
    "yt_documenter": "[Scientific claim] — [Surprising detail]",
    "yt_funny": "[Relatable situation]: [Tarsier twist]",
    "yt_anthro": "[Human situation] ft. [Tarsier character]",
    "yt_pov": "Day [N]: [Atmospheric teaser]",
    "yt_drama": "Episode [N]: [Dramatic title]",
    "fb_fanspage": "[Shocking fact hook]",
}

# Metadata title formula prompts for Gemini
METADATA_TITLE_PROMPTS = {
    "yt_documenter": 'Title MUST follow the formula: "[Scientific claim] — [Surprising detail]". Example: "Tarsier Eyes Are Fixed in Their Skull — Here\'s How They See"',
    "yt_funny": 'Title MUST follow the formula: "[Relatable situation]: [Tarsier twist]". Example: "When You\'re Running Late But Also You\'re a Tarsier"',
    "yt_anthro": 'Title MUST follow the formula: "[Human situation] ft. [Tarsier name]". Example: "Gerald the Tarsier\'s First Day at the Office"',
    "yt_pov": 'Title MUST follow the formula: "Day [N]: [Atmospheric teaser]". Example: "Day 47: Something Changed in the Forest Tonight"',
    "yt_drama": 'Title MUST follow the formula: "Episode [N]: [Dramatic title]". Example: "Episode 3: The Sound Came Back"',
    "fb_fanspage": 'Title MUST follow the formula: "[Shocking fact hook]". Example: "This Tiny Primate Has the Largest Eyes of Any Mammal. Here\'s Why."',
}
