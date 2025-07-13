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

# --- Load API Key from secrets ---
co = cohere.Client(st.secrets["api_keys"]["cohere"])

# --- Constants ---
MOODS = ["😌 Calm", "😐 Meh", "😫 Stressed", "😭 Overwhelmed"]
DATA_FILE = "stress_logs.csv"

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

# --- Mood + Emoji Selection ---
mood = st.radio("🧠 Select your current mood:", MOODS)

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
selected_emotions = st.multiselect("🌈 Select how you feel using emojis:", list(emotions.keys()))
emotion_tags = ", ".join([emotions[e] for e in selected_emotions])

# --- Text Inputs ---
user_input = st.text_area("📝 How are you feeling today?", height=150)

# --- Guided Journaling ---
with st.expander("📓 Need Help? Guided Prompts"):
    st.markdown("- What triggered your stress today?")
    st.markdown("- What helped you feel a bit better?")
    st.markdown("- What would you say to a friend feeling this way?")

journal = st.text_area("✍️ Optional journaling space", height=100)

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

# --- Quote Generator (Fixed for Repetition) ---
def generate_quotes(level):
    prompt = f"""Give me 5 unique, fresh, and motivational quotes for someone dealing with {level} level stress.
Each quote should be short (1-2 lines), emotionally uplifting, and appear on a new line."""

    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=200,
        temperature=0.95,
    )
    all_quotes = [q.strip() for q in response.generations[0].text.strip().split("\n") if q.strip()]
    return random.sample(all_quotes, min(2, len(all_quotes)))

# --- AI Success Story Generator ---
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
            temperature=0.8,
        )
        return response.generations[0].text.strip()
    except Exception:
        fallback_stories = [
            "💼 J.K. Rowling battled depression while on welfare and went on to become a world-famous author.",
            "🧠 Olympic swimmer Michael Phelps faced anxiety and depression but found healing through therapy.",
            "🛠️ Steve Jobs was fired from Apple, the company he founded. He turned failure into fuel for reinvention."
        ]
        return random.choice(fallback_stories)

# --- YouTube Search Links ---
def search_youtube_link(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- Activities ---
def suggest_activities(level):
    if level == "low":
        return ["🌳 Take a short walk", "🎧 Listen to calm music"]
    elif level == "medium":
        return ["🧘 Try a 5-minute meditation", "📋 Prioritize your tasks"]
    else:
        return ["📞 Talk to a friend or therapist", "✍️ Write in your journal or reflect"]

# --- Save Log ---
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

# --- Support Logic ---
if st.button("💡 Get Support"):
    if not user_input.strip():
        st.warning("Please describe how you're feeling.")
    else:
        with st.spinner("Analyzing your stress level..."):
            full_input = user_input + f"\n\n[Emotions: {emotion_tags}]" if emotion_tags else user_input
            level = classify_stress(full_input)

            st.success(f"🧠 Detected Stress Level: **{level.upper()}**")
            log_entry(datetime.now().strftime("%Y-%m-%d"), mood, level, user_input, journal)

            st.subheader("💬 Motivational Quotes")
            quote_placeholder = st.empty()
            quotes = generate_quotes(level)
            for q in quotes:
                quote_placeholder.markdown(f"> {q}")
            if st.button("🔁 Refresh Quotes"):
                quotes = generate_quotes(level)
                quote_placeholder.empty()
                for q in quotes:
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

            st.subheader("🌟 Real Success Story")
            story_placeholder = st.empty()
            story_placeholder.markdown(get_success_story(user_input))
            if st.button("🔁 Refresh Story"):
                story_placeholder.markdown(get_success_story(user_input))

# --- Visualization ---
if os.path.exists(DATA_FILE):
    st.markdown("---")
    st.subheader("📊 Your Stress Log Overview")
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df["stress_score"] = df["stress_level"].map({"low": 1, "medium": 2, "high": 3})
    chart_data = df.groupby("date")["stress_score"].mean()
    st.line_chart(chart_data)

    with st.expander("📜 See Full Journal Log"):
        st.dataframe(df[::-1])

