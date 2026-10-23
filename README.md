# 🎁 GiftGenius: AI Gift Finder

CS4680 Prompt Engineering, AI Assistant Project (MVP)

## The problem
Finding a good gift is hard, and most gift-idea tools return the same generic
list: headset, gift card, mug. The reason is that they only get generic input
("likes gaming"). GiftGenius acts like a good personal shopper. It **asks you
smart follow-up questions first**, then suggests five specific gifts that each
connect to a real detail about the person.

## How it works
1. **Describe the person**: relationship, age, occasion, budget, and what they're into.
2. **The Gift Detective asks 3 follow-up questions**, aimed at whatever your description left out
   (e.g. "Which game does he play the most right now?"). Tap an example answer or type your own.
3. **Get 5 gift cards**, one per tier (Deep Cut, Safe Bet, Wildcard, Experience, Budget / DIY).
   Each card has a price estimate, why it fits, a personal touch, and shopping links.
4. **See what the AI rejected**: the generic ideas it threw out, and why.

## Prompt engineering patterns
All prompts are in [`prompts.py`](prompts.py). The app's "How the prompt works" tab also shows them.

| Pattern | Where | What it does |
|---|---|---|
| **Persona** | `DETECTIVE_SYSTEM`, `GIFT_SYSTEM` | The model plays a "Gift Detective" and an experienced personal shopper who can't stand generic gifts. |
| **Flipped Interaction** | `DETECTIVE_SYSTEM` | The AI asks the user questions before giving any ideas, so it has specific details to work with. |
| **Few-Shot** | both system prompts | Worked examples of bad vs. good questions, and generic vs. genius gifts. |
| **Template** | `DETECTIVE_SCHEMA`, `GIFT_SCHEMA` | The Claude API enforces a JSON schema on the output (structured outputs), so the UI can render cards reliably. |
| **Alternative Approaches** | `TIERS` | Every result covers 5 different kinds of gift instead of 5 variations of one. |
| **Reflection** | `GIFT_SYSTEM` | The model brainstorms 8+ ideas, critiques them, and rejects the 3 most generic. `rejected_ideas` comes before `gifts` in the schema, so it critiques before it answers. |

The app's code also checks the AI's price estimates against your budget and
labels any gift that goes over it.

## Run it locally (Windows)
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\streamlit run main.py
```

**Add your Claude API key** (create one at [platform.claude.com](https://platform.claude.com) and add a few dollars of credit):
copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste your key in.
`secrets.toml` is git-ignored, so the key never reaches GitHub.

Without a key, the app runs in **offline demo mode** using saved example results
(`demo_data.py`). You can also turn demo mode on in the sidebar as a backup if the
Wi-Fi or API fails during a live demo.

## Deploy (publishing bonus)
1. Push this repo to GitHub.
2. On [Streamlit Community Cloud](https://share.streamlit.io), create an app from the repo with `main.py` as the entry point.
3. In the app's **Settings → Secrets**, paste `ANTHROPIC_API_KEY = "your-key"`.

Anyone who opens the public app spends your API credit, so consider setting a
monthly spend limit in the Claude Console.

## Notes
- **Model:** defaults to `claude-opus-5-5`. You can switch to `claude-sonnet-5-5`
  (about half the cost) or `claude-haiku-5-5` (cheapest and fastest) in the sidebar,
  or set `CLAUDE_MODEL` in secrets.
- **Refusal fallback:** on Opus and Sonnet, requests opt into the API's server-side
  fallback (`fallbacks: "default"`), so a request a safety check declines is retried
  on another model instead of failing.
- **Prices are AI estimates.** Check the real price before buying.

## Files
| File | Purpose |
|---|---|
| `main.py` | Streamlit UI: form → detective questions → gift cards |
| `prompts.py` | All prompts, examples, and JSON schemas |
| `claude_client.py` | Claude API calls (Anthropic Python SDK) and friendly error messages |
| `demo_data.py` | Saved example results for offline demo mode |
