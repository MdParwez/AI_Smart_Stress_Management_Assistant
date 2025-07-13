import streamlit as st
import cohere
import random
from datetime import datetime
import pandas as pd
import os

# --- App Config ---
st.set_page_config(page_title="CalmMind AI", page_icon="🧘‍♂️", layout="centered")
co = cohere.Client(st.secrets["api_keys"]["cohere"])

# --- Session State ---
if "stress_level" not in st.session_state:
    st.session_state.stress_level = None
if "quotes" not in st.session_state:
    st.session_state.quotes = []
if "story" not in st.session_state:
    st.session_state.story = ""

# --- Constants ---
MOODS = ["😌 Calm", "😐 Meh", "😫 Stressed", "😭 Overwhelmed"]
DATA_FILE = "stress_logs.csv"
emotions = {
    "😄 Happy": "happy", "😔 Sad": "sad", "😡 Angry": "angry",
    "😰 Anxious": "anxious", "😴 Tired": "tired", "🤯 Overwhelmed": "overwhelmed",
    "😇 Grateful": "grateful", "😕 Confused": "confused"
}

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["🧠 My Support", "📊 Mood Tracker", "📓 Journal Log", "⚙️ Settings"])

with tab1:
    st.title("🧘 CalmMind AI - Your Stress Companion")
    st.markdown("Let’s understand how you’re feeling and support you step-by-step.")

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

    # --- Mood & Emotions ---
    mood = st.radio("🧭 How’s your overall mood today?", MOODS, horizontal=True)
    selected_emotions = st.multiselect("🌈 What emotions are you experiencing right now?", list(emotions.keys()))
    emotion_tags = ", ".join([emotions[e] for e in selected_emotions])

    # --- Input ---
    user_input = st.text_area("📝 Describe what's bothering you or how you're feeling", height=150)
    gratitude = st.text_input("🙏 Something you’re grateful for today (optional)")
    journal = st.text_area("📓 Optional journaling space", height=100)

    # --- Core Functions ---
    def classify_stress(user_input):
        prompt = f"""Classify the following statement into one of these categories: low, medium, or high stress.

Text: "I'm a little anxious but mostly okay"
Stress Level: low

Text: "Deadlines are crushing and I feel overwhelmed"
Stress Level: medium

Text: "I feel lost, alone and mentally drained"
Stress Level: high

Text: "{user_input}"
Stress Level:"""
        response = co.generate(model="command-r-plus", prompt=prompt, max_tokens=1, temperature=0)
        level = response.generations[0].text.strip().lower()
        return level if level in ["low", "medium", "high"] else "medium"

    def generate_quotes(level):
        prompt = {
            "low": "Give me 2 short and light motivational quotes for someone feeling slightly stressed.",
            "medium": "Give 2 strong motivational quotes for someone feeling overwhelmed with work or responsibilities.",
            "high": "Give 2 powerful quotes for someone going through serious emotional stress or burnout.",
        }[level]
        response = co.generate(model="command-r-plus", prompt=prompt, max_tokens=100, temperature=0.9)
        return [line.strip() for line in response.generations[0].text.strip().split("\n") if line.strip()]

    def get_success_story(user_input):
        prompt = f"""
The following person is going through stress: "{user_input}"

Write a calming, realistic, and emotionally comforting success story of someone who went through a similar struggle.
Make it about 150–200 words, and describe how they felt, what small steps they took, and how they slowly healed.
End the story with an uplifting thought that brings peace and hope.
"""
        try:
            response = co.generate(model="command-r-plus", prompt=prompt, max_tokens=250, temperature=0.7)
            return response.generations[0].text.strip()
        except:
            return "🧠 Unable to generate a story. Please try again later."

    def search_youtube_link(query):
        return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

    def log_entry(date, mood, level, user_input, journal):
        row = {
            "date": date,
            "mood": mood,
            "stress_level": level,
            "text": user_input,
            "journal": journal
        }
        df = pd.DataFrame([row])
        if os.path.exists(DATA_FILE):
            df.to_csv(DATA_FILE, mode="a", header=False, index=False)
        else:
            df.to_csv(DATA_FILE, index=False)

    # --- Main Flow ---
    if st.button("💡 Get AI Support"):
        if not user_input.strip():
            st.warning("Please describe how you're feeling.")
        else:
            with st.spinner("Analyzing your stress..."):
                st.session_state.stress_level = classify_stress(user_input)
                st.session_state.quotes = generate_quotes(st.session_state.stress_level)
                st.session_state.story = get_success_story(user_input)
                log_entry(datetime.now().strftime("%Y-%m-%d"), mood, st.session_state.stress_level, user_input, journal)

    if st.session_state.stress_level:
        st.success(f"🧠 Stress Level: **{st.session_state.stress_level.upper()}**")

        st.subheader("💬 Personalized Quotes")
        for quote in st.session_state.quotes:
            st.markdown(f"> {quote}")
        if st.button("🔁 Refresh Quotes"):
            st.session_state.quotes = generate_quotes(st.session_state.stress_level)

        st.subheader("💡 Tips to Try")
        tips = {
            "low": ["🌳 Take a short walk", "🎧 Listen to calm music"],
            "medium": ["🧘 Try a 5-minute meditation", "📋 Prioritize your tasks"],
            "high": ["📞 Talk to a friend or therapist", "✍️ Journal or reflect deeply"]
        }[st.session_state.stress_level]
        for tip in tips:
            st.markdown(f"- {tip}")

        st.subheader("🎥 Watch Helpful Videos")
        query = {
            "low": "relaxing music for stress relief",
            "medium": "guided meditation for work stress",
            "high": "motivational speech for depression"
        }[st.session_state.stress_level]
        story_query = f"real success stories overcoming {st.session_state.stress_level} stress"
        st.markdown(f"🎧 **Feel Better** → [Search YouTube]({search_youtube_link(query)})")
        st.markdown(f"🌟 **Real Stories** → [Search YouTube]({search_youtube_link(story_query)})")

        st.subheader("🌟 Inspired Success Story")
        st.markdown(st.session_state.story)
        if st.button("🔁 Refresh Story"):
            st.session_state.story = get_success_story(user_input)

# --- Mood Tracker ---
with tab2:
    st.subheader("📊 Your Stress Log Overview")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df["date"] = pd.to_datetime(df["date"])
        df["stress_score"] = df["stress_level"].map({"low": 1, "medium": 2, "high": 3})
        st.line_chart(df.groupby("date")["stress_score"].mean())
    else:
        st.info("No log data found yet.")

# --- Journal Log ---
with tab3:
    st.subheader("📓 Your Journal Entries")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        with st.expander("📖 View Full Journal Log"):
            st.dataframe(df[::-1])
    else:
        st.info("No journal entries found yet.")

# --- Future Settings ---
with tab4:
    st.subheader("⚙️ Settings (Coming Soon)")
    st.markdown("🔒 You’ll be able to customize reminders, export logs, and more.")
