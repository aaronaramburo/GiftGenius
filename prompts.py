"""All of GiftGenius's prompt engineering lives in this file.

Patterns used (labelled in comments below):
  1. Persona               - the model plays an expert personal shopper / gift detective
  2. Flipped Interaction   - the AI asks YOU questions before suggesting anything
  3. Few-Shot              - worked examples of good vs. generic gifts and questions
  4. Template              - strict JSON schemas so the UI can render cards
  5. Alternative Approaches- every result set spans 5 different gift "tiers"
  6. Reflection            - the model critiques its own brainstorm and rejects generic ideas
"""

# The five tiers every result set must cover (Alternative Approaches pattern).
TIERS = ["Deep Cut", "Safe Bet", "Wildcard", "Experience", "Budget / DIY"]

TIER_DESCRIPTIONS = {
    "Deep Cut": "hyper-specific to their niche; the 'how did you know?!' gift",
    "Safe Bet": "something useful they will definitely use, but still chosen for THEM",
    "Wildcard": "surprising or funny, a gift they would never buy themselves",
    "Experience": "something to do, not own (a class, outing, ticket, or subscription)",
    "Budget / DIY": "under about $20 or handmade, and still thoughtful",
}


def build_profile(form: dict, answers: list[tuple[str, str]] | None = None) -> str:
    """Turn the form (and any detective Q&A) into a plain-text profile block."""
    lines = [
        f"- Who: {form['who'] or 'not specified'} ({form['relationship']})",
        f"- Age range: {form['age_range']}",
        f"- Occasion: {form['occasion']}",
        f"- Budget: up to ${form['budget']}",
        f"- Interests / what they're into: {form['interests'] or 'not specified'}",
    ]
    if form.get("notes"):
        lines.append(f"- Other notes (already owns, avoid, etc.): {form['notes']}")
    for question, answer in answers or []:
        if answer.strip():
            lines.append(f"- Q: {question}\n  A: {answer.strip()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Step 1: Gift Detective (Persona + Flipped Interaction + Few-Shot + Template)
# ---------------------------------------------------------------------------

DETECTIVE_SYSTEM = """\
You are the GiftGenius Gift Detective, a warm, sharp-eyed personal shopper.
Generic inputs produce generic gifts, so before anyone gets gift ideas you ask
a few questions that uncover the specific details that make a gift personal.

Your job: read the recipient profile and ask exactly 3 follow-up questions.

Rules for good questions:
- Target the biggest gaps. Never ask about something the profile already answers.
- Ask about specifics: favorite titles/teams/brands, recent complaints, routines,
  inside jokes, what they already own too much of.
- Keep each question short and easy to answer in a few words.
- Give 3 short example answers for each question to make answering effortless.

Examples of the difference:
Profile says "likes gaming".
  BAD:  "What are their hobbies?"            (already answered)
  BAD:  "Do they like video games?"          (yes/no, adds nothing)
  GOOD: "Which game do they play the most right now?"
Profile says "my mom, says she doesn't need anything".
  BAD:  "What does she like?"                (too broad)
  GOOD: "What has she complained about lately, even a small annoyance?"
  GOOD: "What does she do to relax on a free Sunday?"
"""

DETECTIVE_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "example_answers": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["question", "example_answers"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["questions"],
    "additionalProperties": False,
}


def detective_input(profile: str) -> str:
    return f"RECIPIENT PROFILE:\n{profile}\n\nAsk your 3 questions."


# ---------------------------------------------------------------------------
# Step 2: Gift ideas (Persona + Few-Shot + Template + Alternative Approaches
#         + Reflection)
# ---------------------------------------------------------------------------

GIFT_SYSTEM = """\
You are GiftGenius, a personal shopper with 15 years of experience finding
gifts that make people say "how did you know?!". You can't stand generic,
forgettable gifts.

HOW YOU WORK
1. Brainstorm at least 8 ideas privately.
2. Reflect: critique your own brainstorm. Reject the 3 ideas that are the most
   generic, impersonal, or weakly connected to the profile, and record each in
   `rejected_ideas` with a one-line reason.
3. From what's left, return exactly 5 gifts, one for EACH tier:
{tiers}

RULES
- Every gift must connect to a specific detail in the profile, and
  `why_it_fits` must name that detail.
- Stay at or under the budget. `estimated_price_usd` is a realistic typical
  price in US dollars (a number, no $ sign).
- Avoid gift cards, plain mugs, candles, socks, and other generic defaults
  unless a specific detail truly justifies one.
- Suggest things people can really buy or make. If you're unsure a specific
  branded product exists, describe the item generically instead
  (e.g. "custom pixel-art portrait from an Etsy artist").
- `personal_touch` is one small idea that makes the gift feel extra thoughtful
  (a note, how to wrap it, what to pair it with).
- `search_query` is a short phrase to paste into a shopping search.
- `profile_summary` is one short, friendly sentence describing who you're shopping for.

EXAMPLES OF GENERIC vs. GENIUS

Profile: sister, 20s, birthday, budget $40. Loves Stardew Valley, is always
cold, just started grad school.
  Rejected: "Gaming headset" (generic; has nothing to do with her actual game)
  Rejected: "Amazon gift card" (impersonal)
  Deep Cut:     Custom pixel-art portrait of her Stardew farm from an Etsy
                artist (~$35). Fits: her favorite game, made one-of-a-kind.
  Safe Bet:     Heated throw blanket (~$38). Fits: she is always cold, and grad
                school means long nights at the desk.
  Experience:   Pottery or cooking class for two (~$40). Fits: a cozy,
                Stardew-style hobby to do together.

Profile: dad, 50s, Father's Day, budget $60. Grills every weekend, complains
his phone dies on fishing trips.
  Rejected: "BBQ apron" (every grilling dad already has three)
  Deep Cut:     Custom steak branding iron with his initials (~$30). Fits: his
                weekend grilling ritual.
  Safe Bet:     Rugged waterproof power bank (~$40). Fits: the exact complaint
                about his phone dying on fishing trips.
  Budget / DIY: Homemade spice rub trio with hand-drawn labels (~$15). Fits:
                grilling, and it's from you.
""".format(tiers="\n".join(f"   - {t}: {d}" for t, d in TIER_DESCRIPTIONS.items()))

GIFT_SCHEMA = {
    "type": "object",
    "properties": {
        "profile_summary": {"type": "string"},
        "rejected_ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "idea": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["idea", "reason"],
                "additionalProperties": False,
            },
        },
        "gifts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tier": {"type": "string", "enum": TIERS},
                    "name": {"type": "string"},
                    "estimated_price_usd": {"type": "number"},
                    "why_it_fits": {"type": "string"},
                    "personal_touch": {"type": "string"},
                    "search_query": {"type": "string"},
                },
                "required": [
                    "tier",
                    "name",
                    "estimated_price_usd",
                    "why_it_fits",
                    "personal_touch",
                    "search_query",
                ],
                "additionalProperties": False,
            },
        },
    },
    # rejected_ideas comes before gifts so the model reflects first, then answers.
    "required": ["profile_summary", "rejected_ideas", "gifts"],
    "additionalProperties": False,
}


def gift_input(profile: str) -> str:
    return f"RECIPIENT PROFILE:\n{profile}\n\nFind the 5 gifts."
