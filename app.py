import streamlit as st
import cohere
import random
from datetime import datetime
import pandas as pd
import os

# --- Config ---
st.set_page_config(page_title="Stress Management AI", page_icon="🧘", layout="centered")
st.title("🧠 Stress Management Assistant")
st.markdown("Describe your stress, track your feelings, and get AI-powered support.")

# --- Load API Key ---
co = cohere.Client(st.secrets["api_keys"]["cohere"])

# --- Session State Initialization ---
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
    "😄 Happy": "happy",
    "😔 Sad": "sad",
    "😡 Angry": "angry",
    "😰 Anxious": "anxious",
    "😴 Tired": "tired",
    "🤯 Overwhelmed": "overwhelmed",
    "😇 Grateful": "grateful",
    "😕 Confused": "confused",
}

# --- Affirmation ---
affirmations = [
    "You are doing the best you can. And that’s enough.",
    "Every breath you take is a step toward peace.",
    "You are stronger than you think.",
    "One small step at a time.",
    "Progress, not perfection.",
]
today = datetime.now().day
st.info(f"🌞 Daily Affirmation: *{affirmations[today % len(affirmations)]}*")

# --- Mood & Input ---
mood = st.radio("📊 What's your overall mood today?", MOODS)
selected_emotions = st.multiselect("🌈 What specific emotions are you feeling right now?", list(emotions.keys()))
emotion_tags = ", ".join([emotions[e] for e in selected_emotions])

user_input = st.text_area("📝 How are you feeling today?", height=150)
journal = st.text_area("📓 Optional journaling space", height=100)

# --- Classify Stress ---
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

    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=1,
        temperature=0,
    )
    level = response.generations[0].text.strip().lower()
    return level if level in ["low", "medium", "high"] else "medium"

# --- Generate Quotes ---
def generate_quotes(level):
    prompt = {
        "low": "Give me 2 short and light motivational quotes for someone feeling slightly stressed.",
        "medium": "Give 2 strong motivational quotes for someone feeling overwhelmed with work or responsibilities.",
        "high": "Give 2 powerful quotes for someone going through serious emotional stress or burnout.",
    }[level]

    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=100,
        temperature=0.9,
    )
    return [line.strip() for line in response.generations[0].text.strip().split("\n") if line.strip()]

# --- YouTube Link ---
def search_youtube_link(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- AI Success Story ---
def get_success_story(user_input):
    prompt = f"""
The following person is going through stress: "{user_input}"

Write a calming, realistic, and emotionally comforting success story of someone who went through a similar struggle.
Make it about 150–200 words, and describe how they felt, what small steps they took, and how they slowly healed.
End the story with an uplifting thought that brings peace and hope.
Do not mention it's fictional or written by AI.
"""
    try:
        response = co.generate(
            model="command-r-plus",
            prompt=prompt,
            max_tokens=250,
            temperature=0.7,
        )
        return response.generations[0].text.strip()
    except:
        return random.choice([
            "💼 *J.K. Rowling* battled depression while on welfare and went on to become a world-famous author.",
            "🧠 Olympic swimmer *Michael Phelps* faced anxiety and depression but found healing through therapy.",
            "🛠️ *Steve Jobs* was fired from Apple, the company he founded. He turned failure into fuel for reinvention."
        ])

# --- Suggestions ---
def suggest_activities(level):
    return {
        "low": ["🌳 Take a short walk", "🎧 Listen to calm music"],
        "medium": ["🧘 Try a 5-minute meditation", "📋 Prioritize your tasks"],
        "high": ["📞 Talk to a friend or therapist", "✍️ Write in your journal or reflect"],
    }[level]

# --- Log Entry ---
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

# --- Analyze & Display ---
if st.button("💡 Get Support"):
    if not user_input.strip():
        st.warning("Please describe how you're feeling.")
    else:
        with st.spinner("Analyzing your stress..."):
            full_input = user_input + f"\n\n[Emotions: {emotion_tags}]" if emotion_tags else user_input
            level = classify_stress(full_input)

            st.session_state.stress_level = level
            st.session_state.quotes = generate_quotes(level)
            st.session_state.story = get_success_story(user_input)

            st.success(f"🧠 Detected Stress Level: **{level.upper()}**")
            log_entry(datetime.now().strftime("%Y-%m-%d"), mood, level, user_input, journal)

# --- Show Results (if any) ---
if st.session_state.stress_level:
    level = st.session_state.stress_level

    st.subheader("💬 Motivational Quotes")
    quote_placeholder = st.empty()
    for q in st.session_state.quotes:
        quote_placeholder.markdown(f"> {q}")
    if st.button("🔁 Refresh Quotes"):
        st.session_state.quotes = generate_quotes(level)
        quote_placeholder.empty()
        for q in st.session_state.quotes:
            quote_placeholder.markdown(f"> {q}")

    st.subheader("💡 Suggested Activities")
    for tip in suggest_activities(level):
        st.markdown(f"- {tip}")

    query = {
        "low": "relaxing music for stress relief",
        "medium": "guided meditation for work stress",
        "high": "motivational speech for depression"
    }[level]
    story_query = f"real success stories overcoming {level} stress"

    st.subheader("🎥 Explore Helpful Videos")
    st.markdown(f"🎧 [Feel Better Videos]({search_youtube_link(query)})")
    st.markdown(f"🌟 [Watch Real Stories]({search_youtube_link(story_query)})")

    st.subheader("🌟 Real Success Story (Inspired by your situation)")
    story_placeholder = st.empty()
    story_placeholder.markdown(st.session_state.story)
    if st.button("🔁 Refresh Story"):
        st.session_state.story = get_success_story(user_input)
        story_placeholder.markdown(st.session_state.story)

# --- Journal Log ---
if os.path.exists(DATA_FILE):
    st.markdown("---")
    st.subheader("📊 Your Stress Log Overview")
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df["stress_score"] = df["stress_level"].map({"low": 1, "medium": 2, "high": 3})
    st.line_chart(df.groupby("date")["stress_score"].mean())

    with st.expander("📜 See Full Journal Log"):
        st.dataframe(df[::-1])
