import streamlit as st
import cohere
import random
from datetime import datetime
import pandas as pd
import os

# --- Page Config ---
st.set_page_config(page_title="StressEase AI", page_icon="🧘", layout="wide")

# --- Theme Toggle (optional) ---
theme = st.selectbox("🎨 Choose Theme:", ["Dark", "Light"], index=0)
dark_mode = theme == "Dark"

# --- Styles ---
PRIMARY = "#00d0b3" if dark_mode else "#0077cc"
BG = "#1e1e2f" if dark_mode else "#f5f5f5"
TEXT = "#ffffff" if dark_mode else "#000000"
CONTAINER_BG = "#2c2c3c" if dark_mode else "#ffffff"

st.markdown(f"""
    <style>
    html, body, .main {{
        background-color: {BG};
        color: {TEXT};
        font-family: 'Segoe UI', sans-serif;
    }}
    .quote-box, .activity-box, .story-box {{
        background-color: {CONTAINER_BG};
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }}
    h1, h2, h3 {{
        color: {PRIMARY};
    }}
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.title("🧘 StressEase AI – Your Personal Calm Assistant")

# --- Load Cohere ---
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
    "One small step at a time.",
    "Progress, not perfection.",
]
today = datetime.now().day
st.info(f"🌞 Daily Affirmation: *{affirmations[today % len(affirmations)]}*")

# --- Inputs ---
col1, col2 = st.columns(2)
with col1:
    mood = st.radio("🧠 How are you feeling today?", MOODS, horizontal=True)
with col2:
    spiritual_choice = st.selectbox("📖 Want spiritual insight from:", SPIRITUAL_BOOKS)

user_input = st.text_area("📝 Describe your feelings or stress:", height=150)
journal = st.text_area("📓 Optional Journal Entry", height=100)

# --- Classify Stress ---
def classify_stress(text):
    prompt = f"""Classify the following into low, medium, or high stress:
"Deadlines are crushing me" → medium
"I feel mentally drained and hopeless" → high
"I'm a little anxious but mostly okay" → low
"{text}" →"""
    res = co.generate(model="command-r-plus", prompt=prompt, max_tokens=1, temperature=0)
    level = res.generations[0].text.strip().lower()
    return level if level in ["low", "medium", "high"] else "medium"

# --- Quotes Generator ---
def generate_quotes(level):
    prompts = {
        "low": "Give 2 light quotes for someone feeling slightly stressed.",
        "medium": "Give 2 strong motivational quotes for overwhelmed people.",
        "high": "Give 2 powerful quotes for deep emotional burnout."
    }
    res = co.generate(model="command-r-plus", prompt=prompts[level], max_tokens=100, temperature=0.9)
    return [q.strip("- ") for q in res.generations[0].text.strip().split("\n") if q.strip()]

# --- Activities + Why They Help ---
def suggest_activities(level):
    if level == "low":
        return [("🌳 Walk outside", "Walking clears the mind and boosts endorphins."),
                ("🎧 Soft music", "Music relaxes your nervous system.")]
    elif level == "medium":
        return [("🧘 Meditation", "Calms racing thoughts and brings balance."),
                ("📋 Break tasks", "Avoid overwhelm by planning step by step.")]
    else:
        return [("📞 Call a friend", "Social support is powerful healing."),
                ("✍️ Journal", "Journaling processes emotions deeply.")]

# --- Story Generator ---
def generate_story(user_input, spiritual_book):
    base_prompt = f"""The user said: "{user_input}".
Write a success story with steps of emotional healing. End with hope.
If possible, include a relevant message from {spiritual_book if spiritual_book != "None" else "a spiritual guide"}."""
    res = co.generate(model="command-r-plus", prompt=base_prompt, max_tokens=300, temperature=0.8)
    return res.generations[0].text.strip()

# --- YouTube ---
def youtube_search_link(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- Save Logs ---
def log_entry(date, mood, level, user_input, journal):
    row = {"date": date, "mood": mood, "stress_level": level, "text": user_input, "journal": journal}
    df = pd.DataFrame([row])
    if os.path.exists(DATA_FILE):
        df.to_csv(DATA_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(DATA_FILE, index=False)

# --- Main Action ---
if st.button("💡 Get Support"):
    if not user_input.strip():
        st.warning("Please describe your feelings first.")
    else:
        with st.spinner("🧠 Thinking deeply..."):
            level = classify_stress(user_input)
            st.success(f"🎯 Stress Level: **{level.upper()}**")
            log_entry(datetime.now().strftime("%Y-%m-%d"), mood, level, user_input, journal)

            # --- Quotes ---
            st.markdown("### 💬 Personalized Quotes")
            for quote in generate_quotes(level):
                st.markdown(f"<div class='quote-box'>💬 {quote}</div>", unsafe_allow_html=True)

            # --- Activities ---
            st.markdown("### 💡 Suggested Activities & Benefits")
            for act, reason in suggest_activities(level):
                st.markdown(f"<div class='activity-box'><b>{act}</b><br><span style='font-size:13px'>{reason}</span></div>", unsafe_allow_html=True)

            # --- Success Story ---
            st.markdown("### 🌟 Real-Life Inspired Story")
            st.markdown(f"<div class='story-box'>{generate_story(user_input, spiritual_choice)}</div>", unsafe_allow_html=True)

            # --- YouTube Links ---
            st.markdown("### 🎥 Explore Videos")
            video_queries = {
                "low": "relaxing stress relief music",
                "medium": "guided meditation anxiety",
                "high": "real depression recovery stories"
            }
            st.markdown(f"🔗 [🎧 Meditation → *{video_queries[level]}*]({youtube_search_link(video_queries[level])})")
            st.markdown(f"🔗 [🌟 Success Videos]({youtube_search_link('success stories about ' + level + ' stress')})")
            if spiritual_choice != "None":
                st.markdown(f"🔗 [📖 {spiritual_choice} Stories]({youtube_search_link(spiritual_choice + ' mental peace')})")

# --- Log Visualization ---
if os.path.exists(DATA_FILE):
    st.markdown("---")
    st.markdown("### 📈 Your Stress Log")
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df["score"] = df["stress_level"].map({"low": 1, "medium": 2, "high": 3})
    st.line_chart(df.groupby("date")["score"].mean())

    with st.expander("📔 Journal Entries"):
        st.dataframe(df[::-1])


