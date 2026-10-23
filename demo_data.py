"""Saved example results so the app works without an API key (and as a
backup if the Wi-Fi or API fails during the live demo)."""

FORM = {
    "who": "my little brother",
    "relationship": "Sibling",
    "age_range": "18-24",
    "occasion": "Birthday",
    "budget": 50,
    "interests": "gaming",
    "notes": "",
}

QUESTIONS = [
    {
        "question": "Which game does he play the most right now?",
        "example_answers": ["Elden Ring", "Minecraft", "Valorant"],
    },
    {
        "question": "Does he mostly play on PC, console, or a handheld?",
        "example_answers": ["PC", "PlayStation", "Nintendo Switch"],
    },
    {
        "question": "What's something about his gaming he's complained about lately?",
        "example_answers": ["Controller drift", "Room too dark", "Battery always dies"],
    },
]

ANSWERS = [
    "Hollow Knight and Elden Ring, he loves really hard games",
    "Nintendo Switch, mostly on the couch",
    "His Switch battery dies on long car rides",
]

GIFTS = {
    "profile_summary": "A 20-something Switch gamer who lives for brutally hard games like Hollow Knight and Elden Ring, and whose battery always dies on road trips.",
    "rejected_ideas": [
        {"idea": "Gaming headset", "reason": "He plays handheld on the couch; nothing in the profile points to audio."},
        {"idea": "Steam gift card", "reason": "Impersonal, and he plays on Switch, not PC."},
        {"idea": "RGB LED light strip", "reason": "A generic 'gamer' gift with no link to the games he loves."},
    ],
    "gifts": [
        {
            "tier": "Deep Cut",
            "name": "Framed Hallownest map art print from an Etsy artist",
            "estimated_price_usd": 30,
            "why_it_fits": "Hollow Knight is his favorite, and the hand-drawn map is the game's most iconic image.",
            "personal_touch": "Mark the spot where he got stuck the longest with a tiny sticker.",
            "search_query": "Hollow Knight Hallownest map art print",
        },
        {
            "tier": "Safe Bet",
            "name": "Compact USB-C power bank that can charge a Switch",
            "estimated_price_usd": 35,
            "why_it_fits": "Solves his exact complaint: the Switch dying on long car rides.",
            "personal_touch": "Hand it over fully charged, with a note: 'No more dead batteries on road trips.'",
            "search_query": "USB-C PD power bank Nintendo Switch",
        },
        {
            "tier": "Wildcard",
            "name": "Desk tally counter labeled 'Deaths This Run'",
            "estimated_price_usd": 12,
            "why_it_fits": "He loves brutally hard games like Elden Ring, where dying is part of the fun.",
            "personal_touch": "Pre-click it to 1 so his first death is already counted.",
            "search_query": "mechanical tally counter clicker",
        },
        {
            "tier": "Experience",
            "name": "Escape room for two",
            "estimated_price_usd": 50,
            "why_it_fits": "A real-life 'boss fight' for someone who loves a hard challenge, and you get to play too.",
            "personal_touch": "Book a room with the highest difficulty rating and call it a raid.",
            "search_query": "escape room near me",
        },
        {
            "tier": "Budget / DIY",
            "name": "Handmade 'Boss Fight Coupons' book",
            "estimated_price_usd": 5,
            "why_it_fits": "Plays on his hard-game obsession and costs almost nothing.",
            "personal_touch": "Include coupons like 'One snack run while you grind' and 'I won't talk during a boss fight'.",
            "search_query": "printable coupon book template",
        },
    ],
}
