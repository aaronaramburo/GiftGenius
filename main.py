"""GiftGenius: an AI gift finder. Run with:  streamlit run main.py"""

import os
from urllib.parse import quote_plus

import streamlit as st

import demo_data
import prompts
from claude_client import (
    DEFAULT_MODEL,
    MODEL_OPTIONS,
    GiftGeniusError,
    ask_questions,
    find_gifts,
)

st.set_page_config(page_title="GiftGenius", page_icon="🎁", layout="wide")

RELATIONSHIPS = ["Friend", "Partner", "Parent", "Sibling", "Kid", "Grandparent", "Coworker", "Other"]
AGE_RANGES = ["Under 12", "12-17", "18-24", "25-34", "35-49", "50-64", "65+"]
OCCASIONS = ["Birthday", "Holiday", "Anniversary", "Graduation", "Thank you", "Just because", "Other"]
TIER_STYLE = {
    "Deep Cut": ("🎯", "violet"),
    "Safe Bet": ("✅", "green"),
    "Wildcard": ("🎲", "orange"),
    "Experience": ("🎟️", "blue"),
    "Budget / DIY": ("✂️", "gray"),
}
PATTERNS = [
    ("Persona", "The AI plays an experienced personal shopper (and a 'Gift Detective' when asking questions)."),
    ("Flipped Interaction", "Before suggesting anything, the AI asks you 3 questions aimed at the gaps in your description."),
    ("Few-Shot", "Both prompts include worked examples of generic vs. genius gifts, and bad vs. good questions."),
    ("Template", "Answers must match a JSON schema (enforced by the Claude API) so the app can draw these cards."),
    ("Alternative Approaches", "Every result covers 5 tiers: Deep Cut, Safe Bet, Wildcard, Experience, Budget / DIY."),
    ("Reflection", "The AI brainstorms 8+ ideas, critiques them, and throws out the 3 most generic (see 'Rejected ideas')."),
]
FORM_KEYS = {field: f"f_{field}" for field in demo_data.FORM}
BLANK_FORM = {"who": "", "relationship": "Friend", "age_range": "18-24", "occasion": "Birthday", "budget": 50, "interests": "", "notes": ""}


def get_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
    except Exception:  # no secrets.toml file
        value = ""
    return value or os.environ.get(name, "")


api_key = get_secret("ANTHROPIC_API_KEY")
state = st.session_state
state.setdefault("stage", "form")
state.setdefault("form", dict(demo_data.FORM if not api_key else BLANK_FORM))


def go(stage: str) -> None:
    state.stage = stage


def start_over() -> None:
    for key in list(state.keys()):
        del state[key]


def load_example() -> None:
    for field, key in FORM_KEYS.items():
        state[key] = demo_data.FORM[field]


# ---------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    if not api_key:
        st.info("No ANTHROPIC_API_KEY found, so the app is running on saved example data. See README.md to add a key.")
    demo = st.toggle(
        "Offline demo mode",
        value=not api_key,
        disabled=not api_key,
        help="Uses saved example results instead of calling Claude. A backup for the live demo.",
    )
    saved_model = get_secret("CLAUDE_MODEL") or DEFAULT_MODEL
    model_choices = MODEL_OPTIONS if saved_model in MODEL_OPTIONS else [saved_model, *MODEL_OPTIONS]
    model = st.selectbox(
        "Claude model",
        model_choices,
        index=model_choices.index(saved_model),
        disabled=demo,
        help="Opus gives the most thoughtful ideas; Sonnet is about half the cost; Haiku is the cheapest and fastest.",
    )
    st.divider()
    st.button("🔄 Start over", on_click=start_over, width="stretch")

# ---------------------------------------------------------------- header
st.title("🎁 GiftGenius")
st.markdown("##### Gifts that make them say *\"how did you know?!\"*")
if demo:
    st.caption("🧪 Offline demo mode: showing a saved example (a little brother who's into gaming).")


def run_search(answers: list[tuple[str, str]]) -> bool:
    """Ask Claude for gifts. Returns True on success."""
    profile = prompts.build_profile(state.form, answers)
    try:
        with st.spinner("🎁 Brainstorming, judging its own ideas, and picking the best 5..."):
            state.results = demo_data.GIFTS if demo else find_gifts(api_key, model, profile)
    except GiftGeniusError as e:
        st.error(str(e))
        return False
    state.profile = profile
    return True


# ---------------------------------------------------------------- step 1: form
def show_form() -> None:
    for field, key in FORM_KEYS.items():
        state.setdefault(key, state.form[field])

    st.button("✨ Fill in an example", on_click=load_example, type="tertiary")
    with st.form("profile_form"):
        c1, c2 = st.columns(2)
        c1.text_input("Who's it for?", key="f_who", placeholder="e.g. my little brother, my mom")
        c2.selectbox("Relationship", RELATIONSHIPS, key="f_relationship")
        c1.selectbox("Age range", AGE_RANGES, key="f_age_range")
        c2.selectbox("Occasion", OCCASIONS, key="f_occasion")
        st.slider("Budget (USD)", 10, 300, step=5, key="f_budget", format="$%d")
        st.text_area(
            "What are they into?",
            key="f_interests",
            placeholder="Hobbies, favorite shows/games/teams, how they spend a free Saturday...",
        )
        st.text_input("Anything to avoid, or that they already have? (optional)", key="f_notes")
        b1, b2 = st.columns(2)
        detective = b1.form_submit_button("🕵️ Ask me smarter questions first", type="primary", width="stretch")
        skip = b2.form_submit_button("Skip, just find gifts", width="stretch")

    if not (detective or skip):
        return
    form = {field: state[key] for field, key in FORM_KEYS.items()}
    if not form["interests"].strip():
        st.warning("Tell me at least one thing they're into. Even \"no idea, she likes coffee\" helps.")
        return
    state.form = form

    if skip:
        state.questions, state.answers = [], []
        if run_search([]):
            go("results")
            st.rerun()
        return

    try:
        with st.spinner("🕵️ The Gift Detective is reading your description..."):
            if demo:
                state.questions = demo_data.QUESTIONS
            else:
                state.questions = ask_questions(api_key, model, prompts.build_profile(form))
    except GiftGeniusError as e:
        st.error(str(e))
        return
    for i in range(len(state.questions)):
        state.pop(f"pill_{i}", None)
        state[f"answer_{i}"] = demo_data.ANSWERS[i] if demo else ""
    go("questions")
    st.rerun()


# ---------------------------------------------------------------- step 2: detective questions
def show_questions() -> None:
    st.subheader("🕵️ A few quick questions")
    st.caption("Specific answers get specific gifts. Tap an example or type your own; skip any you don't know.")

    answers = []
    for i, q in enumerate(state.questions):
        with st.container(border=True):
            st.markdown(f"**{i + 1}. {q['question']}**")
            picked = st.pills("Examples", q.get("example_answers", []), key=f"pill_{i}", label_visibility="collapsed")
            typed = st.text_input("Your answer", key=f"answer_{i}", placeholder="Or type your own answer")
            answers.append((q["question"], typed.strip() or picked or ""))

    b1, b2 = st.columns([1, 3])
    if b1.button("← Edit details"):
        go("form")
        st.rerun()
    if b2.button("🎁 Find gifts", type="primary", width="stretch"):
        state.answers = answers
        if run_search(answers):
            go("results")
            st.rerun()


# ---------------------------------------------------------------- step 3: results
def shop_links(gift: dict) -> None:
    query = quote_plus(gift["search_query"])
    c1, c2 = st.columns(2)
    if gift["tier"] == "Experience":
        c1.link_button("🔎 Search", f"https://www.google.com/search?q={query}", width="stretch")
    else:
        c1.link_button("🛍️ Google", f"https://www.google.com/search?tbm=shop&q={query}", width="stretch")
        c2.link_button("📦 Amazon", f"https://www.amazon.com/s?k={query}", width="stretch")


def gift_card(gift: dict, budget: int) -> None:
    icon, color = TIER_STYLE.get(gift["tier"], ("🎁", "gray"))
    price = gift["estimated_price_usd"]
    with st.container(border=True, height="stretch"):
        st.badge(gift["tier"], icon=icon, color=color)
        st.markdown(f"#### {gift['name']}")
        price_row = st.container(horizontal=True)
        price_row.markdown(f"**~${price:,.0f}**")
        # The model's prices are estimates, so the app double-checks the budget itself.
        if price > budget:
            price_row.badge("Over budget", color="red")
        st.markdown(f"**Why it fits:** {gift['why_it_fits']}")
        st.markdown(f"**Personal touch:** {gift['personal_touch']}")
        shop_links(gift)


def show_results() -> None:
    results = state.results
    order = {tier: i for i, tier in enumerate(prompts.TIERS)}
    gifts = sorted(results.get("gifts", []), key=lambda g: order.get(g.get("tier"), 99))

    st.success(f"**Shopping for:** {results.get('profile_summary', '')}", icon="🎯")

    ideas_tab, prompt_tab = st.tabs(["🎁 Gift ideas", "🔍 How the prompt works"])

    with ideas_tab:
        for row in (gifts[:3], gifts[3:]):
            for col, gift in zip(st.columns(3), row):
                with col:
                    gift_card(gift, state.form["budget"])
        rejected = results.get("rejected_ideas", [])
        if rejected:
            with st.expander(f"🗑️ Ideas GiftGenius rejected ({len(rejected)})"):
                for r in rejected:
                    st.markdown(f"- ~~{r['idea']}~~: {r['reason']}")
        st.caption("Prices are AI estimates. Check the real price before buying.")

    with prompt_tab:
        st.markdown("GiftGenius combines **six prompt engineering patterns**:")
        st.table({"Pattern": [p for p, _ in PATTERNS], "How GiftGenius uses it": [d for _, d in PATTERNS]}, hide_index=True)
        with st.expander("Profile sent to Claude this time"):
            st.code(state.profile, language=None, wrap_lines=True)
        with st.expander("Gift Detective system prompt"):
            st.code(prompts.DETECTIVE_SYSTEM, language=None, wrap_lines=True)
        with st.expander("GiftGenius system prompt"):
            st.code(prompts.GIFT_SYSTEM, language=None, wrap_lines=True)

    st.divider()
    b1, b2, b3 = st.columns(3)
    if b1.button("🔁 Different ideas, same person", width="stretch"):
        if run_search(state.get("answers", [])):
            st.rerun()
    if b2.button("✏️ Change the details", width="stretch"):
        go("form")
        st.rerun()
    b3.button("🆕 New person", on_click=start_over, width="stretch")


{"form": show_form, "questions": show_questions, "results": show_results}[state.stage]()
