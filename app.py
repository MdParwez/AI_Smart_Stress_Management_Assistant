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

# --- Constants ---
MOODS = ["😌 Calm", "😐 Meh", "😫 Stressed", "😭 Overwhelmed"]
BOOKS = ["None", "Quran", "Bible", "Bhagavad Gita", "Buddhist Teachings"]
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
mood = st.radio("🧠 Select your current mood:", MOODS)
spiritual_choice = st.selectbox(
    "📖 Do you want support rooted in a spiritual or religious tradition?",
    BOOKS
)
user_input = st.text_area("📝 How are you feeling today?", height=150)
journal = st.text_area("📓 Optional journaling space (Write anything on your mind)", height=100)

# --- Stress Classification ---
def classify_stress_with_prompt(user_input):
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
        max_tokens=120,
        temperature=random.uniform(0.6, 0.95),
    )
    return [line.strip() for line in response.generations[0].text.strip().split("\n") if line.strip()]

# --- YouTube Search ---
def search_youtube_link(query, book=None):
    if book and book != "None":
        query += f" {book} teaching"
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- Story Generator with Religious Option ---
def generate_story_with_quote(user_input, book):
    prompt = f"""
A person is facing this challenge: "{user_input}".

1. Write a comforting success story (~150 words) about someone who overcame similar stress.
2. Use warm, healing language.
"""
    if book != "None":
        prompt += f"""
3. Include a key idea or quote from the {book} that helped guide them.
4. Make the quote blend naturally into the story — don't cite it formally.
"""

    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=300,
        temperature=0.9
    )
    return response.generations[0].text.strip()

# --- Suggest Activities with Explanation ---
def suggest_activities(level):
    if level == "low":
        return [
            "🌳 Take a short walk — reconnecting with nature calms the mind.",
            "🎧 Listen to calm music — it helps regulate mood and soothe nerves."
        ]
    elif level == "medium":
        return [
            "🧘 Try a 5-minute meditation — mindfulness can reduce anxiety.",
            "📋 Prioritize tasks — breaking down work reduces overwhelm."
        ]
    else:
        return [
            "📞 Talk to a friend or therapist — emotional expression is vital.",
            "✍️ Journal your feelings — writing provides emotional clarity."
        ]

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

# --- Get Support Button ---
if st.button("💡 Get Personalized Support"):
    if not user_input.strip():
        st.warning("Please describe how you're feeling.")
    else:
        with st.spinner("Analyzing your emotions..."):
            try:
                stress_level = classify_stress_with_prompt(user_input)
                st.success(f"🧠 Detected Stress Level: **{stress_level.upper()}**")

                # Log user input
                log_entry(datetime.now().strftime("%Y-%m-%d"), mood, stress_level, user_input, journal)

                # Quotes
                st.subheader("💬 Personalized Quotes")
                for quote in generate_quotes(stress_level):
                    st.markdown(f"> {quote}")

                # Activities
                st.subheader("💡 Suggested Activities & Reasoning")
                for tip in suggest_activities(stress_level):
                    st.markdown(f"- {tip}")

                # Video Sections
                st.subheader("🎥 Explore Related Videos")

                feel_better_query = {
                    "low": "relaxing music for stress relief",
                    "medium": "how to manage work stress",
                    "high": "emotional healing through spirituality"
                }[stress_level]

                st.markdown(f"🎧 **Feel Better Videos** → [Search: *{feel_better_query}*]({search_youtube_link(feel_better_query)})")

                story_query = f"real success stories overcoming {stress_level} stress"
                st.markdown(f"🌟 **Real-Life Comebacks** → [Search: *{story_query}*]({search_youtube_link(story_query)})")

                if spiritual_choice != "None":
                    spiritual_query = f"healing from stress using {spiritual_choice}"
                    st.markdown(f"📖 **Spiritual Insights** → [Search: *{spiritual_query}*]({search_youtube_link(spiritual_query)})")

                # Story
                st.subheader("🌟 Real Success Story (Inspired by your situation)")
                st.markdown(generate_story_with_quote(user_input, spiritual_choice))

            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- History & Chart ---
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

