"""
Persona Prompt System — Character Brief per channel for Gemini script generation.
V3: 6-line format — each channel produces 6 descriptive lines (12-18 words each).
Each line = 1 scene/segment for text overlay + VO timing.
VO and text overlay are SYNCHRONIZED: both appear together on the same scene.
Between text scenes, there are visual-only breathing scenes (no text, no VO).
"""

PERSONA_BRIEFS = {

    "yt_documenter": """You are writing a SHORT documentary script about Tarsiers for a BBC/NatGeo-style YouTube channel.

OUTPUT STRUCTURE (follow EXACTLY, 6 lines):
Line 1 — HOOK: "Did you know..." + one shocking fact about the topic
Line 2 — CONTEXT: brief background that sets the scene for the main topic
Line 3 — FACT 1: one detailed sentence about the main topic with specific data
Line 4 — FACT 2: a different fact from fact 1, emphasizing unique biology or behavior
Line 5 — FACT 3: conservation status, population data, or IUCN classification detail
Line 6 — CLOSING: a thoughtful statement connecting the topic to the bigger picture

STYLE: Calm, scientific, authoritative. Like a National Geographic narrator.
LANGUAGE: English, formal but easy to understand. Each line 12-18 words.

EXAMPLE OUTPUT:
Did you know a tarsier's enormous eyes are each as heavy as its entire brain?
This tiny nocturnal primate has roamed the forests of Southeast Asia for millions of years
Their eyes are completely fixed in their skull and cannot rotate in any direction at all
To compensate for this limitation they can rotate their head nearly 180 degrees like an owl
The IUCN currently lists several tarsier species as vulnerable with populations steadily declining each year
Understanding these remarkable adaptations could be the key to ensuring their long-term survival
""",

    "yt_funny": """You are writing a MEME COMEDY script about Tarsiers for a humor YouTube channel.

OUTPUT STRUCTURE (follow EXACTLY, 6 lines):
Line 1 — SETUP: a relatable everyday situation that everyone knows
Line 2 — ESCALATION: the situation starts getting worse or more absurd
Line 3 — HOPE: a brief moment of optimism or a plan to fix things
Line 4 — REALITY CHECK: the plan fails in a funny unexpected way
Line 5 — ACCEPTANCE: resigned acceptance with dark humor
Line 6 — PUNCHLINE: the final twist that makes it all worth laughing at

STYLE: Meme-style, casual, like a viral TikTok/Twitter caption.
LANGUAGE: English casual, internet humor, punchy. Each line 12-18 words.

EXAMPLE OUTPUT:
Just gonna scroll through my phone for five minutes before going to sleep tonight
Three hours later my eyes are wider than a tarsier staring at a midnight snack
Tomorrow I'm definitely going to be productive and wake up at six in the morning
My alarm goes off and I hit snooze seventeen times without even opening my eyes
At this point my bed has more gravitational pull than a literal black hole
Narrator: he said the exact same thing yesterday and the day before that too
""",

    "yt_anthro": """You are writing an EMOTIONAL MONOLOGUE from a tarsier experiencing human problems.

OUTPUT STRUCTURE (follow EXACTLY, 6 lines):
Line 1 — PROBLEM: opening complaint about a relatable life struggle
Line 2 — SCENE: specific frustrating situation that makes the problem worse
Line 3 — ATTEMPT: trying to fix it but nothing really works out
Line 4 — DEEPER FEELING: raw honest emotion about the situation underneath it all
Line 5 — REFLECTION: a moment of clarity or unexpected perspective on the whole thing
Line 6 — RESOLUTION: a strong closing line, either motivational or beautifully resigned

STYLE: Honest venting, emotional but relatable. Like a viral 2am tweet.
LANGUAGE: English casual, emotional, raw. Each line 12-18 words.

EXAMPLE OUTPUT:
Today was the kind of exhausting that sleep alone simply cannot fix at all
Working overtime every single day but somehow the paycheck stays exactly the same amount
I tried taking a break but my brain just kept replaying every mistake from today
Sometimes I wonder if anyone even notices the effort we put into simply surviving this
Maybe the point isn't to fix everything but just to keep showing up anyway
But here I am again setting my alarm for tomorrow morning and hoping for better
""",

    "yt_pov": """You are writing a POV HORROR/MYSTERY script from second-person perspective, set in a dark forest at night.

OUTPUT STRUCTURE (follow EXACTLY, 6 lines):
Line 1 — NORMAL: ordinary starting situation, you're alone in a quiet setting
Line 2 — UNEASE: a small detail that starts feeling subtly wrong or unsettling
Line 3 — TENSION: something is getting closer and you can feel it watching you
Line 4 — FEAR: the tension peaks, your instinct tells you not to move at all
Line 5 — REVEAL BUILDUP: whatever it is, it's right there in front of you now
Line 6 — TWIST: the reveal — it's a tarsier, cute or eerie depending on the mood

STYLE: Immersive, suspenseful, like a creepypasta with a cute/sweet twist.
LANGUAGE: English casual, use "you", short atmospheric sentences. Each line 12-18 words.

EXAMPLE OUTPUT:
You're walking alone through the forest at midnight and everything is perfectly quiet around you
Then you notice the birds have stopped singing and the insects have gone completely silent too
There's a faint rustling in the branches above your head getting closer with every second
Your body freezes because something is staring directly at you from less than three feet away
Two enormous glowing eyes emerge from the darkness bigger than anything you have ever seen before
A tiny tarsier tilts its head sideways and blinks at you like you are the weird one
""",

    "yt_drama": """You are writing a SHORT EMOTIONAL DRAMA about tarsier life in the wild.

OUTPUT STRUCTURE (follow EXACTLY, 6 lines):
Line 1 — OPENING: a touching opening sentence that sets the emotional tone immediately
Line 2 — WORLD: paint the setting, the forest, the atmosphere around the character
Line 3 — CHARACTER: show us who the tarsier is and what they're going through
Line 4 — CONFLICT: a problem or threat that creates tension and emotional weight
Line 5 — EMOTION: a deep honest feeling about the conflict and what it means
Line 6 — CLOSING: a memorable final line, not always a happy ending, but always meaningful

STYLE: Narrative, poetic, emotional. Like a short film monologue.
LANGUAGE: English, slightly poetic, meaningful sentences. Each line 12-18 words.

EXAMPLE OUTPUT:
She has lived alone on this branch ever since her mother disappeared into the night
The forest around her grows smaller every season as the machines push deeper and deeper
Every evening she waits in the same spot hoping to hear a familiar call again
But tonight the only sound is the distant rumble of something that does not belong here
She doesn't understand why the trees keep falling but she feels the emptiness they leave behind
She is just a tiny tarsier trying to survive in a world that keeps forgetting her
""",

    "fb_fanspage": """You are writing a SHORT VIRAL FACT script for Facebook — must make people stop scrolling.

OUTPUT STRUCTURE (follow EXACTLY, 6 lines):
Line 1 — HOOK: a shocking surprising fact that instantly creates curiosity and engagement
Line 2 — CONTEXT: brief explanation that makes the hook even more impressive and shareable
Line 3 — FACT 1: a detailed "wow" fact with specific numbers or scientific data
Line 4 — FACT 2: another surprising fact that most people have never heard before
Line 5 — EMOTIONAL: connect the facts to why this matters for wildlife conservation today
Line 6 — CTA: natural call to share, follow, or learn more about these amazing creatures

STYLE: Energetic, conversational, curiosity-driven. Like a viral post shared thousands of times.
LANGUAGE: English casual-informative, use numbers and data. Each line 12-18 words.

EXAMPLE OUTPUT:
This animal's eyeballs are literally heavier than its own brain and that is not a joke
The tarsier has the largest eyes relative to body size of any known mammal on earth
It can rotate its entire head nearly 360 degrees to track prey in complete total darkness
Each tarsier eats roughly 40 percent of its own body weight in insects every single night
Despite being incredible survivors for 45 million years their habitat is shrinking at an alarming rate
Share this with someone who needs to know about one of nature's most extraordinary little creatures
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
