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
    "Did you know a tarsier's eyes are each as heavy as its entire brain inside its skull\nThis tiny nocturnal primate has been roaming the forests of Southeast Asia for millions of years\nIts eyes are completely fixed in their skull and cannot rotate in any direction at all\nTo compensate for this limitation it can rotate its head nearly 180 degrees like an owl\nThe IUCN currently lists several tarsier species as vulnerable with populations steadily declining each year\nUnderstanding these remarkable adaptations could be the key to ensuring their long-term survival worldwide",

    "Did you know tarsiers can leap up to 40 times their own body length in one jump\nTheir powerful hind legs contain elongated tarsal bones that function like biological spring mechanisms\nIn total darkness these tiny hunters locate prey using only their extraordinary sense of hearing\nEach ear can move independently to pinpoint the exact location of insects in pitch black forests\nThe Philippine tarsier population is currently estimated at just 5000 to 10000 individuals in the wild\nWithout urgent conservation action these incredible leapers may disappear from our forests within a generation",

    "Did you know tarsiers communicate using ultrasonic sound completely beyond the range of human hearing\nTheir vocalizations can reach frequencies of 91 kilohertz while humans can only hear up to 20 kilohertz\nThis ultrasonic ability lets them coordinate with each other without alerting nearby predators to their presence\nScientists only discovered this remarkable communication system in 2012 after decades of studying these primates\nBefore this discovery researchers thought tarsiers were unusually quiet animals that rarely vocalized at all\nThis finding changed everything we thought we knew about primate communication in the natural world entirely",

    "Did you know the tarsier is the only fully carnivorous primate species alive on Earth today\nIt eats absolutely nothing but live prey including insects small lizards frogs and even small birds\nA single tarsier can consume roughly 10 percent of its entire body weight in prey every night\nTheir hunting strategy involves sitting perfectly still on a branch until prey passes within striking distance\nThe critically endangered Siau Island tarsier has fewer than 5000 individuals remaining in the wild today\nProtecting their forest habitat is the most important step toward saving this unique predator from extinction",

    "Did you know tarsiers have existed on Earth for approximately 55 million years of evolutionary history\nFossil records show their basic body plan has barely changed since the Eocene epoch millions of years ago\nAncestral tarsier species once thrived across North America Europe and Asia during warmer prehistoric climates\nToday all surviving tarsier species are found only on the islands of Southeast Asia and nowhere else\nTheir incredible evolutionary stability suggests they found a survival strategy so perfect it never needed improvement\nStudying these living fossils helps scientists understand how primates evolved into the diverse group we see today",

    "Did you know a newborn tarsier weighs roughly 25 percent of its mother's total body weight at birth\nIn human terms that would be equivalent to giving birth to a baby weighing about 35 pounds immediately\nRemarkably newborn tarsiers can grip branches with their tiny fingers from the very first moment of life\nMothers invest enormous energy in each offspring because they can only produce one baby every six months\nThis slow reproduction rate makes tarsier populations extremely vulnerable to any decline in their forest habitat\nEvery single baby tarsier that survives to adulthood represents a critical victory for the entire species future",

    "Did you know that tarsiers can actually die from psychological stress alone in captivity or disturbance\nLoud sudden noises can trigger fatal cardiac arrest in these extremely sensitive and fragile tiny primates\nThat is exactly why tarsier sanctuaries in Bohol Philippines enforce strict whisper-only rules for all visitors\nCapturing tarsiers from the wild for the illegal pet trade remains a serious ongoing problem across Southeast Asia\nMost captive tarsiers refuse to eat and many die within weeks due to the extreme stress of confinement\nThese animals remind us that some creatures simply cannot survive outside their natural forest homes no matter what",

    "Did you know each individual tarsier eye weighs approximately the same as its entire brain combined together\nAt roughly 16 millimeters wide each massive eye is permanently locked in place within the skull bone structure\nTo look in any direction other than straight ahead a tarsier must rotate its entire head completely around\nIts retina contains one of the highest densities of rod cells found in any mammal species ever studied\nThis gives them extraordinary night vision capable of detecting movement in light levels as low as 0.001 lux\nThese biological adaptations make the tarsier one of nature's most perfectly designed nocturnal predators ever evolved",

    "Did you know tarsiers have the longest fingers relative to their body size of any living primate species\nTheir elongated third finger is approximately as long as their entire forearm creating an incredible gripping tool\nThese specialized fingers are perfect for maintaining a secure hold on thin branches in complete darkness\nTarsiers spend almost their entire lives high up in the trees rarely if ever descending to the ground\nTheir arboreal lifestyle means that deforestation doesn't just reduce their habitat it eliminates their entire world\nEvery tree that falls in a tarsier forest takes with it a piece of their ancient and irreplaceable home",

    "Did you know the tarsier holds the record as one of the world's smallest living primate species today\nIt weighs just 85 to 160 grams making it lighter than most smartphones you carry in your pocket\nYet despite its incredibly tiny size it is one of the most efficient nocturnal predators alive anywhere\nIts hunting success rate in darkness rivals that of predators many hundreds of times its own body weight\nDeforestation and the illegal wildlife trade remain the two biggest threats to tarsier survival across all populations\nProtecting these remarkable miniature primates means protecting the ancient forests they have called home for millennia",
]



# ========================================================
# YT_FUNNY — Setup → Scene → Expectation → Punchline
# ========================================================
FUNNY_SCRIPTS = [
    "Just gonna rest my eyes for 5 minutes before getting up and being productive\nThree hours later and I'm still wide awake scrolling through absolutely nothing useful\nTomorrow I'm definitely going to fix my sleep schedule and be responsible\nThe alarm goes off and I hit snooze so fast my finger broke the sound barrier\nAt this point my bed has more gravitational pull than a literal black hole\nNarrator: tomorrow he said the exact same thing he says every single night",

    "I said just 5 more minutes of this show before I go to sleep tonight\nOne more episode turned into an entire season finished before sunrise somehow\nTomorrow morning I'll wake up early and be the person I always pretend to be\nWoke up late for work again and my boss is already sending passive aggressive texts\nAt this point my Netflix account has more screen time than my actual job does\nBoss: this is the third time this week and it's only Tuesday morning",

    "Starting my diet on Monday for real this time no more excuses from me\nBy Monday lunch I already ordered a double cheeseburger with extra fries on the side\nIt's just one cheat meal it doesn't count if you don't post it online right\nBy dinner I'm eating ice cream straight from the tub watching cooking competition shows\nMy gym membership is paying for itself in guilt alone at this exact moment\nNarrator: this was the 47th consecutive Monday he promised would be different from the rest",

    "Paycheck just hit my account this morning and I felt rich for about five seconds\nAfternoon I was just casually browsing online definitely not adding things to cart at all\nI'll only buy the things I really need like this third pair of identical sneakers\nBy evening my bank balance was so low it started sending me motivational quotes instead\nI checked my account three times hoping the numbers would magically change back somehow\nMy bank app sent a notification that just said are you absolutely sure about your life choices",

    "Told my friends I'm doing totally fine and everything is completely under control right now\nMeanwhile I've been overthinking since 11 PM creating problems that don't even exist yet\nMaybe if I just organize my thoughts everything will make sense and I'll feel better\nI made a to-do list about my anxiety and somehow that just made the anxiety worse\nNow I'm anxious about being anxious which is a level I didn't know was even possible\nMy brain needs a premium subscription with an off switch to stop doing this every night",

    "You know that feeling when you wake up energized and ready to conquer the world today\nYeah me neither I haven't felt that since approximately the third grade or something similar\nSeven alarms and I can still ignore every single one of them without even opening my eyes\nI tried putting my phone across the room but I just crawled back into bed anyway\nThis pillow has its own gravitational field and I am just a helpless satellite orbiting around\nScientists should study my ability to sleep through anything it's genuinely record-breaking at this point",

    "Planned to start my assignment at 8 AM sharp with coffee ready and motivation loaded up\n8 AM opened my laptop and by 9 AM I somehow ended up deep in YouTube rabbit holes\nNoon panic set in because there were exactly 2 hours until the absolute final deadline\nI typed so fast my keyboard started smoking and autocorrect gave up trying to help me\nResult: 3 pages written in exactly 30 minutes fueled entirely by pure concentrated fear and adrenaline\nProfessor: surprisingly this is your best work yet and honestly that makes me question everything",

    "My friend said my resting face looks absolutely terrifying and asked if I was okay today\nBut I was actually in a great mood this is just what my face does naturally\nI tried smiling more but apparently that looked even more concerning to everyone around me\nNow people ask if I'm plotting something every time I try to look approachable and friendly\nThis is just my default expression okay I promise I'm not planning anything at all\nTarsier: finally someone who truly understands the struggle of having a permanently intense face",

    "Set my alarm for 5 AM to go running because today is the day everything changes forever\n5 AM turned off alarm and went back to sleep faster than my motivation disappeared completely\n10 AM woke up feeling guilty about not running but not guilty enough to actually do it\nLooked at my running shoes by the door and they looked just as disappointed in me as I am\nI told myself I'd go for an evening run instead knowing full well that was a complete lie\nTomorrow will definitely be different said me every single day for the past eleven straight months",

    "Bought a brand new planner to finally get my entire life organized and under full control\nFirst week I wrote detailed color-coded plans with stickers and everything looked absolutely perfect on paper\nSecond week the planner became an expensive coffee coaster sitting under my favorite morning mug\nBy week three I couldn't even find it under the pile of things I planned to organize\nThe planner is now judging me silently from underneath a stack of unread self-help books\nBest investment: currently collecting dust on my shelf right next to last year's unused planner too",
]



# ========================================================
# YT_ANTHRO — Problem → Scene → Complaint → Resolution
# ========================================================
ANTHRO_SCRIPTS = [
    "Today was exhausting beyond words and I don't even know where the energy went\nWorking overtime every day but the paycheck stays exactly the same every single month\nI tried talking to someone about it but they just said everyone goes through this phase\nSometimes I just want to quit everything and disappear to somewhere nobody can find me\nMaybe the point isn't to feel okay all the time but to keep going even when it hurts\nBut here I am setting my alarm for tomorrow morning and hoping something feels different",

    "Tired of pretending to be strong all the time when everything inside feels like crumbling\nEveryone thinks I'm perfectly fine because I learned how to smile on autopilot years ago\nI tried letting my guard down once but they used my honesty against me later that week\nBut inside I'm falling apart piece by piece and nobody seems to notice or even care\nMaybe vulnerability isn't weakness but I'm still too scared to test that theory out again\nWho would even want to listen when everyone else is fighting their own battles right now",

    "Working hard but nobody even notices the extra hours and the effort behind the scenes\nThe one who got promoted just talks the loudest not works the hardest in this office\nI tried speaking up in a meeting today but my voice got drowned out by louder ones\nI want to scream but the words just won't come out like my throat is made of glass\nMaybe being quiet doesn't mean being invisible but it sure feels like that most days\nGuess this is just how the world works and some of us are stuck learning it the hard way",

    "I just want some time for myself but everyone keeps needing something from me constantly\nFrom morning to night taking care of everyone else's problems and forgetting about my own\nI tried saying no today and the guilt hit me harder than the exhaustion ever did before\nWhen I need someone they all disappear like I'm only useful when I'm giving not receiving\nMaybe self-care isn't selfish but the world keeps making me feel guilty for wanting it\nSomeday I'll learn to put myself first without feeling like I'm letting everyone down around me",

    "Sometimes I feel like I'm never enough no matter how hard I try or how much I give\nNo matter what I do it always feels like less than what was expected of me today\nI tried celebrating a small win but my brain immediately reminded me of ten bigger failures\nTired of chasing standards I didn't even set while watching everyone else make it look so easy\nMaybe enough isn't about achievements or numbers but about being at peace with who I am\nI'm still learning that lesson and honestly some days I believe it and some days I don't",

    "Everyone seems to know their purpose in life and exactly where they're heading with confidence\nI'm still figuring out what I even want while pretending I have a five year plan ready\nI tried making a list of my goals but the page stayed blank for twenty whole minutes\nGetting older but the direction is still unclear and the pressure keeps building up every day\nMaybe it's okay not to have all the answers as long as I keep asking the questions\nGuess I'll just keep walking forward and hope I recognize the destination when I finally arrive there",

    "Want to talk but scared of being a burden to the people I care about the most\nSo I keep it all inside until it suffocates me and the silence becomes its own weight\nI tried writing it down once but reading my own words back made everything feel too real\nSmiling outside but there's a storm on the inside that nobody gets to see ever at all\nMaybe carrying everything alone isn't strength but I don't know any other way to survive this\nWhen can I be completely honest without being judged or told that I'm being too dramatic about it",

    "Failed again today despite giving everything I had and leaving nothing in reserve at all\nTried my absolute hardest and it still wasn't enough to meet the bar they set for me\nI keep telling myself that failure is just a lesson but some lessons hurt way too much\nIt feels like running on a treadmill going nowhere while everyone else is sprinting past me fast\nMaybe success isn't a straight line but I wish someone had warned me about all the detours\nBut at least I'm still running and I haven't stopped yet and maybe that's enough for today",

    "Missing home but I have to stay here because the bills won't pay themselves on their own\nFar from family just trying to make a living in a city that doesn't even know my name\nI tried calling home today but hearing their voices made me miss them even more than before\nSome nights feel longer than they should when you're lying awake counting ceiling tiles alone again\nMaybe distance makes the heart grow stronger not just fonder because mine feels heavy every night\nHope all of this sacrifice means something someday when I look back and see how far I came",

    "Body is tired but my mind is even more exhausted from carrying thoughts that weigh too much\nSleep doesn't come easy anymore because my brain replays every conversation from the past week nonstop\nI tried meditation and deep breathing but my anxiety laughed and turned up the volume even louder\nWaking up in the morning feels impossibly heavy like gravity decided to work double shifts on me\nMaybe rest isn't about sleeping but about finding peace with the chaos inside my own head\nBut life keeps moving forward whether I want it to or not so I guess I keep moving too",
]



# ========================================================
# YT_POV — Normal → Scene → Tension → Reveal
# ========================================================
POV_SCRIPTS = [
    "You're walking alone through the forest at midnight and everything around you is perfectly quiet\nThe birds stopped singing about ten minutes ago and even the insects have gone completely silent now\nThere's a faint rustling in the branches directly above your head getting closer with each passing second\nYour body freezes because something is staring directly at you from less than three feet away up there\nTwo enormous glowing eyes emerge slowly from the darkness bigger than anything you have ever seen before\nA tiny tarsier tilts its head sideways and blinks at you like you are the weird one standing here",

    "The night feels wrong somehow and the forest is way too quiet for this time of the evening\nUsually there are crickets chirping everywhere but right now there is only an unsettling deep silence around you\nYou turn around slowly and something moves in the branches just barely visible in the pale moonlight above\nEvery instinct in your body tells you not to move a single muscle because you are being watched right now\nA pair of impossibly large eyes appear floating in the darkness where no eyes should logically be at all\nJust a tiny tarsier sitting there perfectly still staring at you like it has been expecting your arrival tonight",

    "You wake up in your tent at exactly 2 AM because something outside just made a sound you've never heard\nThere's a small shadow moving on the other side of the fabric casting strange shapes from the moonlight\nA soft scratching sound runs along the tent wall from one corner to the other painfully slow and deliberate\nYour heart is pounding so hard you can hear it echoing inside your own skull right now in the silence\nYou reach for the zipper and pull it open with shaking hands not sure what you're about to find outside\nA tiny tarsier face stares back at you from six inches away looking almost as surprised as you are right now",

    "You're walking through the Bohol forest completely alone at night with only a dim flashlight guiding your way\nThe trees around you are swaying gently back and forth but there is absolutely no wind blowing at all tonight\nSomething leaps from branch to branch directly above your head moving faster than your eyes can track properly\nYou point your flashlight up and the beam catches something small with enormous reflective eyes staring straight back\nIt doesn't move and it doesn't blink and for a moment you forget that you're supposed to be the bigger one\nA night hunter smaller than your entire hand has been following you through this forest the whole time tonight",

    "You hear a sound but you cannot figure out where it is coming from or what could possibly be making it\nThe frequency feels strange and wrong like it's vibrating inside your skull instead of passing through your ears\nYou spin around trying to locate the source but the forest looks empty in every direction you can see\nTurns out the sound is completely beyond the range of what human ears are designed to detect or process\nTarsiers are calling to each other in ultrasonic frequencies all around you but you can't hear a single one\nYou've been surrounded by invisible conversations this entire time and you had absolutely no idea until right now",

    "You find tiny tracks pressed deeply into the moss growing on the trunk of an ancient tree in the dark\nLong delicate finger marks with an impossibly strong grip pattern carved into the bark like tiny claw scratches\nBelow the tracks are the scattered remains of a large insect's exoskeleton picked completely clean of all flesh\nWhatever killed this insect did it with surgical precision and strength far beyond what something this small should have\nThe world's smallest predator had its dinner right here on this exact branch while you were sleeping in your tent\nYou realize you've been camping ten feet from a tiny apex predator and you never even knew it was there",

    "You set up your infrared camera deep in the forest because you want to capture whatever moves after midnight\nAt 3 AM there's a sudden flash of movement across the screen so fast the camera almost didn't catch it\nSomething impossibly small launches itself six feet through pitch black air without a single sound or hesitation at all\nThe footage shows a creature with eyes that take up half its entire face locked onto a moth mid-flight perfectly\nIn one frame the moth exists and in the next frame it's gone captured by jaws that moved faster than lightning\nA tarsier catches its prey in complete darkness with an accuracy that would make any predator on Earth jealous tonight",

    "You sit perfectly still beneath a tree in total darkness because your guide told you not to move no matter what\nSomething begins descending slowly down the trunk beside you so close you can feel the bark shifting slightly nearby\nIts head rotates a full 180 degrees and two massive unblinking eyes lock directly onto your face without warning\nYou stop breathing because the eyes are so large and so close that they fill your entire field of vision completely\nFor three full seconds neither of you moves and the forest holds its breath along with both of you together\nA tarsier the size of a tennis ball decides you're boring and climbs back up the tree without a second glance",

    "You're night hiking through dense jungle when your flashlight suddenly dies and the forest goes completely pitch black instantly\nYou stand frozen in place because you can't see your own hand even when you hold it directly in front of your face\nA tiny sound comes from right next to your left ear so close you can almost feel the vibration on your skin\nYou're afraid to turn your head because whatever it is sounds like it's sitting on the branch at exactly your height\nVery slowly you pull out your phone and activate the screen light illuminating a pair of enormous golden eyes watching\nA small tarsier sits on a branch six inches from your face looking at you with an expression of pure calm curiosity",

    "You enter a small limestone cave in Sulawesi in the late afternoon just as the light outside begins to fade away\nOn the cave ceiling above you there are dozens of tiny points of reflected light clustered together in the shadows\nAt first you think they're fireflies or mineral crystals or maybe condensation droplets catching the last rays of daylight\nBut then one pair of lights blinks and then another pair blinks and then all of them start blinking at different times\nYou realize you're standing underneath an entire colony of sleeping tarsiers and every single one is now awake staring down\nTarsier eyes reflecting your flashlight beam as they wake up for the night shift like tiny living stars on the ceiling",
]



# ========================================================
# YT_DRAMA — Opening → Scene → Conflict → Emotion → Closing
# ========================================================
DRAMA_SCRIPTS = [
    "She has lived alone on this branch ever since her mother disappeared into the darkness one night\nThe forest around her used to be vast and full of sounds that meant safety and belonging and home\nEvery evening she waits in the same exact spot hoping to hear a familiar call echoing through the trees\nBut the forest grows smaller every season and the sound of machines is getting closer each passing day\nShe doesn't understand why the trees keep falling but she feels the emptiness they leave behind in the air\nShe is just a tiny tarsier trying to survive in a world that keeps forgetting she even exists at all",

    "This forest used to stretch for miles in every direction as far as any tarsier eye could ever see\nNow the trees fall one by one around her and the sky gets wider in places it never should have been\nShe doesn't understand why her home is disappearing or where the familiar sounds have gone this season\nAll she knows is that tonight feels colder than any night before and the silence is heavier than usual\nShe holds her baby closer to her chest because the branch they're sitting on trembles when trucks pass below\nTomorrow even this branch might be gone and she has nowhere else to take her only child to sleep safely",

    "She gave birth during the heaviest monsoon rains the island had seen in the past twenty years at least\nHer baby was impossibly tiny but its fingers gripped her fur with a strength that surprised even her\nThat first night the mother did not sleep at all she only watched and listened and held on tight together\nThe rain hammered down and the branches swayed but she kept her body between the storm and her child\nThe world outside doesn't care about creatures this small living their entire lives in trees nobody thinks about\nBut a mother's love doesn't need anyone's permission or approval to be the fiercest force in nature tonight",

    "He is the oldest tarsier left in his group and every night he remembers there used to be more\nOne by one the others left this part of the forest and not a single one of them ever came back\nNow it's just him and the silence that fills the space between the trees where their calls used to echo\nHe still hunts every night with the same precision and patience he learned when he was barely months old\nBut his eyes aren't as sharp as they used to be and the moths seem faster than he remembers them being\nStill he climbs to the highest branch every evening because stopping has never been something tarsiers understand",

    "That night he heard a sound that he had never known before in all his years living in this forest\nIt wasn't a predator and it wasn't the wind and it wasn't rain falling on the canopy leaves above him\nA bright unnatural light cut through the ancient darkness of his forest like nothing he had ever experienced before\nHe leaped to the highest branch he could reach pressing his tiny body flat against the bark in fear\nBut the light kept getting closer and the ground beneath the tree began to shake and vibrate with heavy machinery\nBy morning the tree next to his was gone and the sky had a hole in it where branches used to be",

    "They had been together through two full seasons calling to each other at frequencies only they could hear\nEvery dusk she would call and he would answer and the forest between them would hum with their connection\nUntil one night the call from her side of the forest was not returned no matter how long he waited\nHe called again and again until his tiny lungs burned and the morning light started creeping through the branches\nThe forest answered him with nothing but silence and the distant sound of something that didn't belong there\nShe never came back and he still calls for her every single night from the same branch they used to share",

    "Her baby fell from a branch while learning to leap and two meters felt like a cliff for that tiny body\nThe mother dove down after it faster than gravity should allow pushing through leaves and vines without hesitation\nShe caught her baby three inches from the ground with fingers that gripped harder than anything in that moment\nIn the wild there is no room for a second chance and one mistake can mean the end of everything\nBut tonight failure didn't mean the end and her baby clung to her fur shaking but breathing and alive\nShe carried it back up to the highest branch and didn't let go for the rest of that entire night",

    "His territory was taken last week by a younger stronger male who arrived from the other side of the ridge\nHe didn't fight back because his body isn't what it used to be and tarsiers know when they are outmatched\nHe moved to the edge of the forest where the trees are thinner and the insects are harder to find\nIn this new place no one recognizes his calls and no one answers when he cries out into the darkness\nThe loneliness of starting over in a place where you don't belong weighs more than his entire small body does\nBut tarsiers don't know the meaning of giving up so he hunts and he waits and he keeps on going alone",

    "The rain hasn't stopped for three straight days and the insects are hiding deep inside the bark and soil\nHis stomach has been empty since yesterday and the cold is making his tiny muscles cramp with every movement\nHe sits curled inside a hollow in an ancient tree trunk pressing himself against the wood for any warmth available\nThe cold reaches deep into his fragile bones and his heartbeat slows to conserve whatever energy he has left\nHe knows that when the rain stops he must hunt immediately or his body will simply stop working altogether\nTomorrow he will either eat or he won't and that simple fact is the only truth in this tiny life",

    "They captured him during the day while he was sleeping peacefully in the hollow he had used for three years\nLarge unfamiliar hands reached into the darkness and closed around his tiny body before he could even react to flee\nHe didn't fight back because tarsiers don't fight they just freeze and their massive eyes go wide with pure terror\nHis heart beat far too fast for something so small pounding at over 300 beats per minute from the stress alone\nInside the cage his enormous eyes searched for trees that weren't there and darkness that wouldn't come to hide him\nSome tarsiers never come back from human hands and the ones that do are never quite the same as before",
]


# ========================================================
# FB_FANSPAGE — Hook → Fact 1 → Fact 2 → CTA
# ========================================================
FB_SCRIPTS = [
    "This animal's eyeballs are literally heavier than its own brain and that is not even a joke at all\nThe tarsier has the largest eyes relative to body size of any mammal species ever recorded on Earth\nIt can rotate its entire head nearly 360 degrees to track and hunt prey in complete total darkness\nEach tarsier eats roughly 40 percent of its own body weight in live insects every single night without fail\nDespite being incredible survivors for over 45 million years their habitat is shrinking at an alarming rate today\nShare this with someone who needs to know about one of nature's most extraordinary little creatures right now",

    "This primate weighs less than your phone but can jump 40 times its own body length in one leap\nThe tarsier tips the scales at just 85 to 160 grams making it one of the smallest primates alive today\nIt's the only primate species on Earth that is completely 100 percent carnivorous eating nothing but live prey\nIts hunting accuracy in pitch darkness rivals that of predators hundreds of times larger and more powerful than itself\nIllegal wildlife trafficking remains one of the biggest threats to tarsier populations across all of Southeast Asia today\nTag a friend who didn't know this incredible tiny predator even existed somewhere out there in the world tonight",

    "This animal can talk but humans literally cannot hear a single word of what it says to other tarsiers\nTarsiers communicate using ultrasonic sound frequencies reaching up to 91 kilohertz way beyond human hearing ability completely\nThis secret communication channel lets them coordinate hunts and warn each other without any predators eavesdropping at all\nScientists only discovered this remarkable ability in 2012 after decades of assuming tarsiers were mostly silent creatures overall\nMost people have never even heard of tarsiers despite them being one of nature's most fascinating evolutionary success stories\nFollow this page for more incredible animal facts that will make you see the natural world completely differently from now",

    "A tarsier can literally die if you shout too loudly near it because its nervous system is that sensitive\nExtreme sudden stress can trigger fatal cardiac arrest in these incredibly tiny and fragile little primate creatures instantly\nThat's exactly why tarsier sanctuaries in Bohol Philippines enforce strict whisper-only rules for every single visitor who enters\nMost captive tarsiers refuse to eat and many tragically die within just weeks from the overwhelming stress of confinement\nThese animals are a powerful reminder that some wild creatures can never be turned into pets no matter how cute\nShare this so more people understand why tarsier conservation and leaving them in the wild matters so much today",

    "This animal the size of your fist has been alive on Earth for 55 million years longer than most mammals\nTarsier fossils show their basic body design has barely changed since the Eocene epoch millions of years ago naturally\nAncestral tarsiers once lived across North America and Europe back when those continents were covered in tropical forests everywhere\nToday all surviving tarsier species exist only on a handful of islands across Southeast Asia and absolutely nowhere else\nTheir incredible evolutionary stability proves they found a survival strategy so perfect that nature never needed to change it\nLike and share if you just learned that this tiny creature is literally older than the Himalayas and the Alps combined",

    "A newborn tarsier weighs 25 percent of its mother's total body weight which is absolutely insane when you think about it\nIn human terms that would be equivalent to a woman giving birth to a baby weighing about 35 pounds immediately\nRemarkably these tiny newborns can grip tree branches with their miniature fingers from the very first second of being alive\nBut mothers can only produce one single baby every six months making each offspring critically important to the species survival\nWith deforestation destroying their homes at record rates every baby tarsier that survives is a small miracle for conservation efforts\nShare this incredible fact with your friends because most people have never heard anything this amazing about any animal before",

    "The tarsier has the sharpest night vision of any primate species with eyes perfectly designed for total darkness hunting\nIts retina is packed with the highest density of specialized rod cells found in virtually any mammal species ever studied\nIt can successfully hunt and catch live prey in darkness levels as impossibly low as just 0.001 lux of light\nEach eye is permanently locked in its skull and weighs roughly the same as the tarsier's entire brain does combined\nTo compensate for eyes that cannot move at all it rotates its entire head nearly 180 degrees like an owl can\nFollow this page for amazing animal facts every single day that will blow your mind and teach you something new",

    "The tarsier might be the most efficient predator on the planet when measured relative to its tiny body size overall\nIn a single night one individual tarsier eats approximately 10 percent of its entire body weight in live caught prey\nIt catches fast-moving insects and even small birds completely mid-air in total darkness without making any sound whatsoever at all\nIts reaction time is faster than most predators ten times its size giving it an extraordinary advantage as a nocturnal hunter\nYet despite these incredible abilities tarsier populations continue declining because humans keep destroying the forests they depend on to live\nTag a friend who loves learning about unique animals and help spread awareness about these amazing tiny predators right now today",
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
