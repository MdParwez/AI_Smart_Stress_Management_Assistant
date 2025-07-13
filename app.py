import streamlit as st
import cohere
import random
from datetime import datetime
import pandas as pd
import os

# --- Config ---
st.set_page_config(page_title="CalmMind AI", page_icon="🧘", layout="wide")

# --- Theme Colors (Dark Only) ---
PRIMARY = "#00d0b3"
BG = "#1e1e2f"
TEXT = "#ffffff"
CONTAINER_BG = "#2c2c3c"

# --- Custom CSS ---
st.markdown(f"""
    <style>
    html, body, .main {{
        background-color: {BG};
        color: {TEXT};
        font-family: 'Segoe UI', sans-serif;
    }}
    h1, h2, h3 {{
        color: {PRIMARY};
    }}
    .quote-box, .activity-box, .story-box {{
        background-color: {CONTAINER_BG};
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    </style>
""", unsafe_allow_html=True)

# --- App Title ---
st.markdown("<h1 style='text-align:center;'>🧘 CalmMind AI – Your Personal Emotional Wellness Guide</h1>", unsafe_allow_html=True)
st.markdown("### Track your mood, receive support, and discover peace.")

# --- Load API Key ---
co = cohere.Client(st.secrets["api_keys"]["cohere"])

# --- Constants ---
MOODS = ["😌 Calm", "😐 Meh", "😫 Stressed", "😭 Overwhelmed"]
SPIRITUAL_BOOKS = ["None", "Bhagavad Gita", "Bible", "Quran", "Buddhist Texts"]
DATA_FILE = "stress_logs.csv"

# --- Daily Affirmation ---
affirmations = [
    "You are doing the best you can. And that’s enough.",
    "Every breath you take is a step toward peace.",
    "You are stronger than you think.",
    "Progress, not perfection.",
    "You are loved, even when it feels quiet.",
    "There’s peace waiting on the other side of this moment.",
    "It’s okay to rest. That’s where healing happens.",
    "Storms pass. You will find the sun again.",
]
random.seed(datetime.now().day)
today_affirmation = random.choice(affirmations)
st.info(f"🌞 *Affirmation of the Day:* **{today_affirmation}**")

# --- Input Fields ---
col1, col2 = st.columns(2)
with col1:
    mood = st.radio("🧠 How are you feeling today?", MOODS, horizontal=True)
with col2:
    spiritual_choice = st.selectbox("📖 Want support from spiritual books?", SPIRITUAL_BOOKS)

user_input = st.text_area("📝 Describe your current thoughts or stress:", height=150)
journal = st.text_area("📓 Optional journal space:", height=100)

# --- Stress Classifier ---
def classify_stress(text):
    prompt = f"""Classify this into low, medium, or high stress.
"I'm a little anxious but mostly okay" → low
"Deadlines are crushing me" → medium
"I feel mentally drained and hopeless" → high
"{text}" →"""
    res = co.generate(model="command-r-plus", prompt=prompt, max_tokens=1, temperature=0)
    level = res.generations[0].text.strip().lower()
    return level if level in ["low", "medium", "high"] else "medium"

# --- Quote Generator ---
def generate_quotes(level):
    prompts = {
        "low": "Give 2 calming quotes for someone mildly stressed.",
        "medium": "Give 2 strong motivational quotes for someone overwhelmed.",
        "high": "Give 2 powerful quotes for emotional burnout and sadness."
    }
    res = co.generate(model="command-r-plus", prompt=prompts[level], max_tokens=100, temperature=0.9)
    return [q.strip("- ") for q in res.generations[0].text.strip().split("\n") if q.strip()]

# --- Activities ---
def suggest_activities(level):
    if level == "low":
        return [("🌳 Go outside", "Fresh air and movement help clear your mind."),
                ("🎧 Calm music", "Gentle rhythms reduce cortisol levels.")]
    elif level == "medium":
        return [("🧘 5-min meditation", "Brings awareness back to the present."),
                ("🗂️ Break your tasks", "Reduces overwhelm by managing focus.")]
    else:
        return [("📞 Talk to someone", "Support systems are vital for mental health."),
                ("✍️ Write your emotions", "Journaling provides safe expression.")]

# --- Success Story ---
def generate_story(user_input, book):
    prompt = f"""The user said: "{user_input}".
Write a success story showing emotional healing. Use hope and emotional strength. Include a relevant message or reference from {book if book != 'None' else 'a wise person'} if appropriate."""
    res = co.generate(model="command-r-plus", prompt=prompt, max_tokens=300, temperature=0.8)
    return res.generations[0].text.strip()

# --- YouTube Search ---
def youtube_search_link(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- Log Entry ---
def log_entry(date, mood, level, text, journal):
    row = {"date": date, "mood": mood, "stress_level": level, "text": text, "journal": journal}
    df = pd.DataFrame([row])
    if os.path.exists(DATA_FILE):
        df.to_csv(DATA_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(DATA_FILE, index=False)

# --- Support Engine ---
if st.button("💡 Get Support"):
    if not user_input.strip():
        st.warning("Please describe your thoughts to begin.")
    else:
        with st.spinner("Analyzing... please wait."):
            level = classify_stress(user_input)
            st.success(f"🎯 Detected Stress Level: **{level.upper()}**")
            log_entry(datetime.now().strftime("%Y-%m-%d"), mood, level, user_input, journal)

            # --- Quotes ---
            st.markdown("### 💬 Motivational Quotes")
            for quote in generate_quotes(level):
                st.markdown(f"<div class='quote-box'>💬 {quote}</div>", unsafe_allow_html=True)

            # --- Activities ---
            st.markdown("### 💡 Suggested Activities & Why")
            for act, reason in suggest_activities(level):
                st.markdown(f"<div class='activity-box'><b>{act}</b><br><span style='font-size:13px'>{reason}</span></div>", unsafe_allow_html=True)

            # --- Story ---
            st.markdown("### 🌟 An Inspired Story for You")
            st.markdown(f"<div class='story-box'>{generate_story(user_input, spiritual_choice)}</div>", unsafe_allow_html=True)

            # --- YouTube Video Links ---
            st.markdown("### 🎥 Helpful Videos")
            query_map = {
                "low": "relaxing music stress relief",
                "medium": "guided meditation for work stress",
                "high": "recovery motivation depression"
            }
            st.markdown(f"🔗 [🎧 Meditation/Music Video]({youtube_search_link(query_map[level])})")
            st.markdown(f"🔗 [🌟 Uplifting Stories]({youtube_search_link('success stories about ' + level + ' stress')})")
            if spiritual_choice != "None":
                st.markdown(f"🔗 [📖 {spiritual_choice} Guidance Videos]({youtube_search_link(spiritual_choice + ' stress wisdom')})")

# --- History Chart ---
if os.path.exists(DATA_FILE):
    st.markdown("---")
    st.markdown("### 📈 Mood and Stress Trends")
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df["score"] = df["stress_level"].map({"low": 1, "medium": 2, "high": 3})
    st.line_chart(df.groupby("date")["score"].mean())

    with st.expander("📔 View Full Journal Log"):
        st.dataframe(df[::-1])



