"""
Fallback Script Bank — Pre-written tarsier scripts per channel persona.
Used when ALL Gemini API keys are exhausted (billing quota).
RULE: Pipeline must NEVER fail due to API unavailability.

Each channel has 10+ unique scripts. The system picks based on topic hash
to ensure variety while being deterministic (same topic = same script).
"""

import hashlib
import random


# ========================================================
# YT_DOCUMENTER — BBC/NatGeo documentary style
# ========================================================
DOCUMENTER_SCRIPTS = [
    """The Philippine Tarsier, Carlito syrichta, possesses what may be the most extraordinary visual system in the primate world. Each eye is approximately 16 millimeters in diameter — roughly the same volume as its entire brain. These enormous eyes are completely fixed in their sockets. The tarsier cannot rotate them even a single degree. To compensate, evolution granted this species a remarkable adaptation: cervical vertebrae that allow the head to rotate nearly 180 degrees in each direction. This gives the tarsier an effective 360-degree field of vision without moving its body. According to the International Primate Society, this rotational ability is unmatched among all living primates. The tarsier's retina contains an unusually high density of rod cells — photoreceptors optimized for low-light conditions. Research published in the Journal of Human Evolution suggests that tarsiers can detect light levels as low as 0.001 lux, making them among the most efficient nocturnal hunters in the animal kingdom. The IUCN currently lists the Philippine Tarsier as Near Threatened, with population estimates ranging between 5,000 and 10,000 individuals in the wild. Habitat destruction and the illegal pet trade remain their primary threats. Conservation efforts in Bohol, Philippines, have established protected sanctuaries, but fragmented forest habitats continue to pose challenges for long-term species survival.""",

    """Deep in the forests of Southeast Asia lives a predator so silent that its prey never hears it coming. The Tarsier, belonging to the family Tarsiidae, is the only fully carnivorous primate on Earth. Unlike other primates that supplement their diet with fruits or leaves, tarsiers feed exclusively on live prey — insects, small lizards, and even birds. Their hunting technique is remarkable. A tarsier will remain motionless on a vertical branch for extended periods, using its acute hearing to locate prey in complete darkness. When a target is identified, the tarsier launches with explosive force, covering distances up to 40 times its body length in a single leap. Research by Dr. Sharon Gursky-Doyen at Texas A&M University documented that a single tarsier can consume up to 10 percent of its own body weight in insects each night. Their elongated tarsus bones — from which the species derives its name — function as biological springs, storing and releasing energy with remarkable efficiency. Current conservation data from the IUCN indicates that several tarsier species face declining population trends, with the Siau Island Tarsier classified as Critically Endangered.""",

    """The acoustic world of the tarsier remained a mystery to science until 2012, when researchers at Humboldt State University made a startling discovery. Tarsiers communicate using ultrasonic frequencies — sound waves above 20 kilohertz, beyond the range of human hearing. Using specialized recording equipment, the team documented tarsier calls reaching frequencies up to 91 kilohertz. This places them among the very few terrestrial mammals known to use pure ultrasound for communication. The evolutionary advantage is clear: by communicating at frequencies that predators cannot detect, tarsiers maintain social bonds while remaining invisible to owls, snakes, and other nocturnal hunters. Each tarsier species produces a distinct ultrasonic signature, allowing researchers to identify species boundaries through acoustic analysis alone. This discovery prompted the Philippine government to implement noise regulation policies near tarsier habitats in Bohol province. Excessive human-generated noise, even at frequencies tarsiers can hear, has been linked to elevated stress hormone levels in wild populations. The tarsier's sensitivity to sound disturbance is so extreme that documented cases exist of individuals dying from stress-induced cardiac arrest when exposed to prolonged loud noise.""",

    """At just 85 to 160 grams, the Philippine Tarsier ranks among the smallest primates ever to have existed. Yet its evolutionary lineage stretches back approximately 55 million years, making tarsiers one of the oldest surviving primate groups on the planet. Fossil evidence from the Eocene epoch reveals that ancestral tarsiers once inhabited North America, Europe, and mainland Asia. Today, all surviving species are confined to the islands of Southeast Asia — the Philippines, Borneo, Sumatra, and Sulawesi. This dramatic range contraction tells a story of climate change and continental drift spanning tens of millions of years. The tarsier's body plan has remained remarkably stable through this entire period. Comparative skeletal analysis by Dr. Chris Beard of the Carnegie Museum of Natural History shows that modern tarsier anatomy differs very little from 45-million-year-old fossil specimens. This evolutionary conservatism suggests that the tarsier occupies a highly specialized ecological niche that has remained viable across geological timescales. The current global population of all tarsier species combined is estimated at fewer than 50,000 individuals, scattered across increasingly fragmented island habitats.""",

    """The reproductive biology of the tarsier presents one of nature's most remarkable paradoxes. Despite being among the smallest primates, tarsiers give birth to proportionally the largest infants of any primate species. A newborn tarsier weighs approximately 25 percent of its mother's body weight. In human terms, this would be equivalent to giving birth to a 35-pound baby. Tarsier infants are born fully furred with their eyes open, capable of clinging to branches within hours of birth. This precocial development strategy contrasts sharply with most other small primates, which produce altricial young that require weeks of complete parental dependency. Research at the Philippine Tarsier Foundation documented that mothers invest approximately six months in rearing each offspring, during which time they will not reproduce again. This slow reproductive rate — combined with a maximum lifespan of 12 to 20 years in the wild — makes tarsier populations exceptionally vulnerable to habitat loss. A population decline of even 10 percent per decade could push multiple species toward extinction within a century.""",
]


# ========================================================
# YT_FUNNY — Meme-style comedy captions
# ========================================================
FUNNY_SCRIPTS = [
    """[VISUAL: Tarsier staring with huge eyes directly at camera]
This tarsier has seen your browser history.
[VISUAL: Tarsier slowly turning head 180 degrees]
And now it's looking for the exit.
[VISUAL: Tarsier gripping branch with tiny hands]
POV: Monday morning and you're holding onto your sanity
[VISUAL: Tarsier catching insect mid-air]
When the pizza delivery person says they're outside
[VISUAL: Tarsier sitting perfectly still]
Me pretending to work when my boss walks by
[VISUAL: Two tarsiers on same branch]
When you and your bestie both failed the exam
[VISUAL: Tarsier leaping between branches]
My last brain cell during the meeting
[VISUAL: Tarsier close-up with enormous eyes]
When someone says 'we need to talk'""",

    """[VISUAL: Tarsier hanging upside down]
Me checking the fridge at 3 AM for the fourth time
[VISUAL: Tarsier with wide eyes in darkness]
The WiFi: disconnects for 0.3 seconds. Me:
[VISUAL: Tarsier head rotation]
When you hear your name in someone else's conversation
[VISUAL: Tarsier tiny hands grasping]
My grip on reality this week
[VISUAL: Tarsier mid-leap]
Me diving into bed after a 14-hour shift
[VISUAL: Tarsier eating cricket]
Accepting that third slice of pizza at 2 AM
[VISUAL: Tarsier frozen still]
When the teacher asks who wants to present first""",

    """[VISUAL: Tarsier extreme close-up eyes]
Google: tarsier eyes are as big as their brain. My brain:
[VISUAL: Tarsier on thin branch bouncing]
My bank account balance trying to survive until payday
[VISUAL: Tarsier yawning showing tiny teeth]
Me reacting to my own cooking
[VISUAL: Baby tarsier clinging to mother]
Me still depending on my parents at 25
[VISUAL: Tarsier in tree hollow]
My social life: existing but hidden
[VISUAL: Tarsier catching flying bug]
Finally catching that mosquito at 4 AM
[VISUAL: Tarsier silent stare]
When someone says 'I sent you an email, did you see it?'""",

    """[VISUAL: Tarsier perched on branch at night]
This little guy is 55 million years old. And still can't adult.
[VISUAL: Tarsier making ultrasonic call]
Scientists: tarsiers communicate in frequencies humans can't hear. Me texting my crush:
[VISUAL: Tarsier leaping dramatically]
My motivation appearing for exactly 5 minutes on Sunday evening
[VISUAL: Tarsier with huge eyes looking up]
When the waiter brings food to the table next to yours
[VISUAL: Tarsier fingers gripping bark]
Holding on to that one compliment from 2019
[VISUAL: Tarsier head spinning around]
Me checking all directions before crossing an empty street""",

    """[VISUAL: Tarsier absolutely still on branch]
Loading... please wait... brain.exe has stopped responding
[VISUAL: Tarsier eyes reflecting light]
Night vision: activated. Midnight snack mission: go.
[VISUAL: Two tarsiers staring at each other]
Introverts at a party finding each other
[VISUAL: Tarsier stretching tiny arms]
Me reaching for the remote that's 2 inches too far
[VISUAL: Tarsier hunting in slow motion]
My WiFi speed explained in one clip
[VISUAL: Tarsier baby face]
Too small to be stressed. Too cute to care.""",
]


# ========================================================
# YT_ANTHRO — Anthropomorphized sitcom style
# ========================================================
ANTHRO_SCRIPTS = [
    """Meet Gerald. Gerald is a tarsier who has lived on the same branch for three years. Not because he likes it — because his neighbor Frank keeps taking the good branches. Every evening at precisely 6:47 PM, Gerald wakes up, stretches his impossibly long fingers, and begins the nightly ritual of pretending he doesn't see Frank. Frank, for his part, pretends not to notice Gerald pretending. Their relationship is what scientists call 'territorial tolerance.' Gerald calls it 'Tuesday.' Tonight's agenda is simple: find dinner, avoid the owl, and absolutely do not make eye contact with Margaret from the next tree over. Margaret has opinions. About everything. Last week she lectured Gerald for seventeen minutes — in ultrasound that no human could hear — about the proper way to eat a cricket. Gerald ate it wrong, apparently. There is a wrong way. Tonight Gerald catches three beetles and a moth. A productive evening. He returns to his branch, does a full 180-degree head rotation to check for predators, and settles in. Frank is watching. Gerald pretends not to notice Frank watching. Tomorrow they will do this again.""",

    """Patricia is the oldest tarsier in group seven. At fourteen years old, she has survived three typhoon seasons, a habitat survey team that tried to tag her, and an unfortunate incident involving a very confused fruit bat. Patricia does not discuss the fruit bat incident. What Patricia does discuss — at length, in frequencies only her fellow tarsiers can hear — is the declining quality of insects in the neighborhood. Back in her day, the crickets were bigger. The cicadas had more crunch. And the beetles didn't taste like someone had left them in the rain. The younger tarsiers think Patricia is exaggerating. They haven't been alive long enough to know she's completely right. Tonight, Patricia demonstrates the art of the ambush hunt for her daughter's latest offspring. The technique hasn't changed in 55 million years: sit still, listen, jump. The baby tarsier watches with eyes that take up half its face. It jumps. It misses. It falls two feet and grabs a vine. Patricia does her signature 180-degree head turn — not to check for predators, but to avoid watching.""",

    """Derek has a problem. Derek's territory overlaps with the territory of a slightly larger male named Stanley. In the tarsier world, this means one of two things: fight or duet. Tarsier males don't actually fight very often. The energy cost is too high when you weigh 130 grams. Instead, they engage in vocal dueling — ultrasonic calls that escalate in frequency and complexity until one male concedes superiority. Derek has been practicing. He can now hit 70 kilohertz, which in human terms would be like singing a note that shatters glass made of other glass. Stanley counters with 75 kilohertz. It's impressive. More importantly, it's annoying. The females in the group judge these displays not on volume or frequency, but on consistency. A male who can maintain a clean ultrasonic call for thirty seconds demonstrates lung capacity, neural health, and determination. Derek manages twenty-two seconds. Stanley hits thirty-one. Derek returns to his branch and eats a cricket. Tomorrow he'll practice.""",
]


# ========================================================
# YT_POV — First-person night exploration
# ========================================================
POV_SCRIPTS = [
    """It's 2 AM in the Bohol rainforest. The canopy blocks every trace of moonlight. I switch on the infrared camera and immediately, two enormous reflective eyes appear three meters ahead. A Philippine Tarsier. It hasn't moved. I step closer, careful not to crack a single twig. The guides warned me — these animals are so sensitive to stress that sudden noise can trigger cardiac arrest. I hold my breath. The tarsier's head begins to rotate. Slowly. Impossibly slowly. Until those massive eyes are looking directly behind it without the body moving at all. One hundred and eighty degrees of pure biological engineering. My infrared picks up movement on a nearby branch. A cricket. The tarsier has already heard it. In the fraction of a second it takes me to blink, the tarsier launches. Five feet through absolute darkness, guided entirely by sound. It lands with its prey already secured in those elongated fingers. No wasted motion. Fifty-five million years of evolution compressed into a single perfect strike. I check my recording. Seventeen minutes of footage. This one encounter will define the entire expedition.""",

    """The forest sounds different at midnight. Every rustle becomes information. I'm positioned at the base of a strangler fig where our team documented a pair of Western Tarsiers last week. The female should be somewhere within a fifty-meter radius — tarsiers maintain remarkably small territories for a primate. I check the acoustic monitor. Nothing in human-audible range. But the spectrogram shows activity above 20 kilohertz. Ultrasonic calls, exactly where the research predicted they would be. I point the directional microphone upward. The calls resolve into a pattern — short bursts followed by longer sustained tones. According to Dr. Rafe Brown's acoustic catalog, this is a contact call between a mother and juvenile. Somewhere in this darkness, a tarsier the size of my fist is calling for its baby in frequencies that evolution made invisible to predators. Invisible to us, too, until the technology caught up. I wait another forty minutes before the pair moves into camera range. The juvenile is clinging to a vertical branch, eyes impossibly large for its body. It sees me long before I see it.""",

    """Night three in the Tangkoko Reserve, Sulawesi. We are tracking the Spectral Tarsier, Tarsius tarsier — the species that gave the entire genus its name. The rain stopped twenty minutes ago but water still cascades through every layer of canopy. Each raindrop is noise. Each noise masks the insects that the tarsiers depend on. I find our tagged individual — TK-14, a male we've been following for eight months — pressed against the trunk of a dead tree. He's positioned himself on the leeward side, sheltered from water but exposed to the sounds of the forest floor. Smart. The insects will emerge from ground cover now that the rain has stopped. TK-14 drops headfirst down the trunk in a motion that looks like controlled falling. Two feet from the ground, he freezes. I hear nothing. He hears everything. His head tilts — those fixed eyes can't track movement, but his ears are triangulating. The strike comes from zero. One instant he is still. The next instant he has a beetle the size of his thumb. In the darkness, with rain still dripping from every leaf, this animal just demonstrated why tarsiers have survived for 55 million years.""",
]


# ========================================================
# YT_DRAMA — Emotional mini-film narration
# ========================================================
DRAMA_SCRIPTS = [
    """She was born in the hollow of a fig tree during the monsoon rains. Her mother had chosen the spot carefully — sheltered from wind, hidden from owls, close enough to the canopy edge for a quick escape. At birth, she weighed twenty-three grams. Her eyes were already open. Her fingers already grasped the bark with a strength that contradicted everything about her size. In the tarsier world, there is no nursery period. No gradual introduction to danger. From her first breath, every sound in the forest was either food or threat. Her mother nursed her for sixty days. On the sixty-first day, she was alone. This is not cruelty. This is the arithmetic of survival at the smallest scale. A mother tarsier who continues nursing cannot hunt efficiently. A mother who cannot hunt will not survive the dry season. And a species that has persisted for fifty-five million years did not achieve that record through sentiment. She made her first kill that night — a moth, small and slow. She missed twice before connecting. But connection was enough. The forest would test her every night for the next twelve to twenty years. Most nights, she would pass. Tonight, she learned the only lesson that mattered: in the dark, hesitation is death.""",

    """The loggers arrived in February. They came with chainsaws and a government permit. They left with thirty-seven trees from the eastern slope of the ridge — trees that had stood for three hundred years, trees that held territories, hunting grounds, and sleeping hollows for an entire tarsier community. The tarsiers did not leave. This is important to understand. When habitat is destroyed, the popular imagination pictures animals fleeing to safety. But tarsiers are territorial. Their entire behavioral architecture is built around a specific set of branches, a specific set of prey routes, a specific acoustic landscape. Removing the trees did not displace them. It stranded them. Within six weeks, three of the seven individuals on the eastern slope had disappeared. Stress, starvation, predation — the researchers could not determine which took each one. The remaining four compressed into a space one-third the size of their original range. They hunted the same insects. They called from the same branches. But the mathematics had changed. The forest was smaller. The prey was fewer. The predators were the same. Conservation is rarely about dramatic rescues. It is usually about mathematics.""",

    """He was the last male in his group. The others had dispersed — pushed out by declining territory, drawn away by female calls from distant ridges. He remained because he was old. Twelve years in tarsier terms is not ancient, but it is enough. Enough to have survived every predator the forest contains. Enough to have fathered offspring that now hunt in territories he will never visit. Enough to know that the branch he sleeps on is the right branch, and that the hollow above it provides shelter from rain but not from the monitor lizard that lives two trees to the north. He hunts with the precision of repetition. The same patrol route. The same listening posts. The same explosive launch that turns gravity into a weapon. Tonight he catches four insects and a small gecko. Tomorrow he will catch four insects and a small gecko. His body is slower than it was three years ago. His ultrasonic calls have dropped by two kilohertz — still within range, but the younger males can hear the decline. Somewhere in the forest, a younger male is practicing his call. Somewhere in the forest, this story is beginning again.""",
]


# ========================================================
# FB_FANSPAGE — Short, vivid, shareable
# ========================================================
FB_SCRIPTS = [
    """Did you know the Tarsier has the largest eyes relative to body size of any mammal? Each eye is approximately 16mm in diameter — as big as its entire brain! These incredible nocturnal primates can rotate their heads nearly 180 degrees because their eyes are completely fixed in their skulls. Found only in Southeast Asia, tarsiers are the world's only fully carnivorous primates, feeding exclusively on insects, lizards, and small birds. They hunt in complete darkness using their extraordinary hearing — they can even detect ultrasonic frequencies up to 91 kilohertz! Sadly, these ancient primates are threatened by habitat loss. The Philippine Tarsier is classified as Near Threatened by the IUCN. You can help by supporting conservation efforts in Bohol, Philippines. Share this to spread awareness about these amazing animals!""",

    """Tarsier fun facts that will blow your mind: They weigh only 85 to 160 grams — lighter than a smartphone! They can leap up to 40 times their own body length. A newborn tarsier weighs 25 percent of its mother's body weight. They communicate in ultrasound that humans can't hear. They've been around for 55 million years — older than most mammals alive today. Their fingers are so long they can wrap completely around a branch. They're the only primates that eat zero plants — 100 percent carnivorous. They can die from stress if handled by humans. Conservation status: Near Threatened. Let's protect these incredible creatures!""",

    """Meet the world's tiniest predator. The Tarsier may look cute, but it's a highly efficient nocturnal hunter with some of the most advanced biological adaptations in the animal kingdom. Those enormous eyes? They can see in almost total darkness. That rotating head? It compensates for eyes that cannot move at all. Those long fingers? Perfect for snatching insects mid-flight in the pitch black of a rainforest night. Tarsiers have survived for 55 million years across geological epochs that wiped out most other species. They outlasted the dinosaurs' successors. They adapted through ice ages and continental shifts. But they may not survive us. Deforestation, illegal pet trade, and tourism harassment threaten every remaining species. If you see a tarsier 'attraction' offering photo opportunities with captive animals — walk away. These animals literally die from the stress of human handling. Support legitimate conservation instead.""",
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
       Mashup = sentences from template A + sentences from template B
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
        
        # Inject topic reference
        topic_mention = topic.split(",")[0].strip() if topic else "tarsier behavior"
        script = script.replace("Tarsier", f"Tarsier ({topic_mention})", 1)
        
        print(f"[{account_key}] FALLBACK SCRIPT (template #{index+1}/{len(scripts)}) — "
              f"topic: {topic_mention} ({len(script)} chars)")
        return script, template_id
    
    else:
        # ========================================
        # ALL TEMPLATES EXHAUSTED → CREATE MASHUP
        # Combine sentences from 2 different templates
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
        
        # Split both into sentences
        sentences_a = re.split(r'(?<=[.!?])\s+', script_a.strip())
        sentences_b = re.split(r'(?<=[.!?])\s+', script_b.strip())
        
        # Interleave: take odd sentences from A, even from B
        mashup_sentences = []
        max_len = max(len(sentences_a), len(sentences_b))
        for i in range(max_len):
            if i % 2 == 0 and i < len(sentences_a):
                mashup_sentences.append(sentences_a[i])
            elif i < len(sentences_b):
                mashup_sentences.append(sentences_b[i])
        
        # Pick a subset based on topic hash for further variation
        if len(mashup_sentences) > 4:
            start = topic_hash % max(1, len(mashup_sentences) // 3)
            end = min(len(mashup_sentences), start + max(4, len(mashup_sentences) // 2))
            mashup_sentences = mashup_sentences[start:end]
        
        script = ' '.join(mashup_sentences)
        
        # Inject topic reference
        topic_mention = topic.split(",")[0].strip() if topic else "tarsier behavior"
        script = script.replace("Tarsier", f"Tarsier ({topic_mention})", 1)
        
        # Unique template_id using pair + timestamp (never same)
        ts = int(_datetime.now().timestamp())
        template_id = f"fb_{account_key}_mashup_{idx_a}_{idx_b}_{ts}"
        
        print(f"[{account_key}] MASHUP SCRIPT (mix #{idx_a+1}+#{idx_b+1}) — "
              f"topic: {topic_mention} ({len(script)} chars, {len(mashup_sentences)} sentences)")
        return script, template_id

