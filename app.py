import streamlit as st
import cohere
import random
from datetime import datetime
import pandas as pd
import os

# --- App Configuration ---
st.set_page_config(page_title="CalmMind AI — Stress Assistant", page_icon="🧘", layout="wide")

# --- Custom CSS ---
st.markdown("""
    <style>
        .big-font { font-size: 22px !important; }
        .section-title {
            font-size: 26px;
            font-weight: 700;
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 10px;
        }
        .quote-box, .story-box {
            background-color: #f4f9f4;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #FFC107;
            margin-bottom: 10px;
        }
        .activity-list {
            font-size: 18px;
            line-height: 1.6;
            margin-bottom: 6px;
        }
    </style>
""", unsafe_allow_html=True)

# --- API Keys ---
co = cohere.Client(st.secrets["api_keys"]["cohere"])
DATA_FILE = "stress_logs.csv"
MOODS = ["😌 Calm", "😐 Meh", "😫 Stressed", "😭 Overwhelmed"]

# --- Affirmation of the Day ---
affirmations = [
    "You are doing the best you can. And that’s enough.",
    "Every breath you take is a step toward peace.",
    "You are stronger than you think.",
    "One small step at a time.",
    "Progress, not perfection.",
]
today = datetime.now().day
st.info(f"🌞 Daily Affirmation: *{affirmations[today % len(affirmations)]}*")

# --- Input Section ---
st.markdown("## 📝 Track Your Mood")
mood = st.radio("How are you feeling today?", MOODS, horizontal=True)
user_input = st.text_area("Describe your current stress or thoughts", height=150)
journal = st.text_area("Optional journaling space", height=100)

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

    response = co.generate(model="command-r-plus", prompt=prompt, max_tokens=1, temperature=0)
    level = response.generations[0].text.strip().lower()
    return level if level in ["low", "medium", "high"] else "medium"

# --- Quotes Generator ---
def generate_quotes(level):
    prompt = {
        "low": "Give me 3 short and light motivational quotes for someone feeling slightly stressed.",
        "medium": "Give 3 strong motivational quotes for someone feeling overwhelmed with work or responsibilities.",
        "high": "Give 3 powerful quotes for someone going through serious emotional stress or burnout.",
    }[level]

    response = co.generate(model="command-r-plus", prompt=prompt, max_tokens=120, temperature=random.uniform(0.6, 1.0))
    return [line.strip("- ") for line in response.generations[0].text.strip().split("\n") if line.strip()]

# --- AI Success Story Generator ---
def get_success_story(user_input):
    prompt = f"""
The following person is going through stress: "{user_input}"

Write a calming, realistic, and emotionally comforting success story of someone who went through a similar struggle.
Make it about 150–200 words, and describe how they felt, what small steps they took, and how they slowly healed.
End the story with an uplifting thought that brings peace and hope.
"""
    try:
        response = co.generate(model="command-r-plus", prompt=prompt, max_tokens=300, temperature=0.7)
        return response.generations[0].text.strip()
    except:
        return "Someone like you went through the same stress. With time, small steps, and belief in themselves — they got better. And you will too."

# --- Activities ---
def suggest_activities(level):
    return {
        "low": ["🌿 Take a walk", "🎧 Listen to calming music"],
        "medium": ["🧘 Try a short meditation", "📋 Write a priority list"],
        "high": ["📞 Talk to a friend or therapist", "✍️ Journal your emotions"]
    }[level]

# --- YouTube Search ---
def search_youtube_link(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- Logging ---
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

# --- Submit Button ---
if st.button("💡 Get Support"):
    if not user_input.strip():
        st.warning("Please describe how you're feeling.")
    else:
        with st.spinner("Analyzing your stress..."):
            level = classify_stress(user_input)
            st.success(f"🧠 Detected Stress Level: **{level.upper()}**")
            log_entry(datetime.now().strftime("%Y-%m-%d"), mood, level, user_input, journal)

            # --- Quotes Section ---
            st.markdown('<div class="section-title">💬 Personalized Quotes</div>', unsafe_allow_html=True)
            for quote in generate_quotes(level):
                st.markdown(f'<div class="quote-box">💭 {quote}</div>', unsafe_allow_html=True)

            # --- Activities ---
            st.markdown('<div class="section-title">💡 Suggested Activities</div>', unsafe_allow_html=True)
            for activity in suggest_activities(level):
                st.markdown(f'<div class="activity-list">✅ {activity}</div>', unsafe_allow_html=True)

            # --- YouTube Links ---
            query = {
                "low": "relaxing music for stress",
                "medium": "guided meditation for stress",
                "high": "motivational talk for burnout"
            }[level]
            story_query = f"real success stories overcoming {level} stress"

            st.markdown('<div class="section-title">🎥 Helpful Resources</div>', unsafe_allow_html=True)
            st.markdown(f"🔎 [Explore calming videos →]({search_youtube_link(query)})")
            st.markdown(f"🌟 [Watch real stress stories →]({search_youtube_link(story_query)})")

            # --- Success Story ---
            st.markdown('<div class="section-title">🌟 Real Success Story (Inspired by You)</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="story-box">{get_success_story(user_input)}</div>', unsafe_allow_html=True)

# --- Log Overview ---
if os.path.exists(DATA_FILE):
    st.markdown("---")
    st.markdown('<div class="section-title">📊 Stress Log Overview</div>', unsafe_allow_html=True)
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df["score"] = df["stress_level"].map({"low": 1, "medium": 2, "high": 3})
    st.line_chart(df.groupby("date")["score"].mean())
    with st.expander("📜 Full Journal"):
        st.dataframe(df[::-1])
