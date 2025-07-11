import streamlit as st
import cohere
import random
from datetime import datetime
import pandas as pd
import os

# --- Mobile Responsive Styling ---
st.markdown("""
<style>
@media (max-width: 768px) {
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    textarea, input, .stButton button {
        font-size: 16px !important;
        padding: 14px 18px !important;
    }
    .stRadio > div {
        flex-direction: column;
    }
}
.stButton button {
    border-radius: 10px;
    background-color: #4CAF50;
    color: white;
    transition: 0.3s;
}
.stButton button:hover {
    background-color: #45a049;
}
</style>
""", unsafe_allow_html=True)

# --- Config ---
st.set_page_config(page_title="Stress Management AI", page_icon="🧘", layout="centered")
st.title("🧠 Stress Management Assistant")
st.markdown("📱 **Tip:** Add this app to your phone’s home screen from your browser for quick access like a mobile app!")
st.markdown("Describe your stress, track your feelings, and get AI-powered support.")

# --- Load API Key from secrets.toml ---
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

# --- Mood & Inputs ---
mood = st.radio("🧠 Select your current mood:", MOODS)
user_input = st.text_area("📝 How are you feeling today?", height=150)
journal = st.text_area("📓 Optional journaling space (Write anything on your mind)", height=100)

# --- Stress Classification with Prompt ---
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
        max_tokens=100,
        temperature=0.8,
    )
    return [line.strip() for line in response.generations[0].text.strip().split("\n") if line.strip()]

# --- YouTube Search Link ---
def search_youtube_link(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

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
            temperature=0.7,
        )
        return response.generations[0].text.strip()
    except Exception:
        fallback_stories = [
            "💼 *J.K. Rowling* battled depression while on welfare and went on to become a world-famous author.",
            "🧠 Olympic swimmer *Michael Phelps* faced anxiety and depression but found healing through therapy.",
            "🛠️ *Steve Jobs* was fired from Apple, the company he founded. He turned failure into fuel for reinvention."
        ]
        return random.choice(fallback_stories)

# --- Activity Suggestions ---
def suggest_activities(level):
    if level == "low":
        return ["🌳 Take a short walk", "🎧 Listen to calm music"]
    elif level == "medium":
        return ["🧘 Try a 5-minute meditation", "📋 Prioritize your tasks"]
    else:
        return ["📞 Talk to a friend or therapist", "✍️ Write in your journal or reflect"]

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

# --- Analyze & Support ---
if st.button("💡 Get Support"):
    if not user_input.strip():
        st.warning("Please describe how you're feeling.")
    else:
        with st.spinner("Analyzing your stress level..."):
            try:
                level = classify_stress_with_prompt(user_input)
                st.success(f"🧠 Detected Stress Level: **{level.upper()}**")

                # Save the entry
                log_entry(datetime.now().strftime("%Y-%m-%d"), mood, level, user_input, journal)

                # Quotes
                st.subheader("💬 Personalized Quotes")
                for quote in generate_quotes(level):
                    st.markdown(f"> {quote}")

                # Suggestions
                st.subheader("💡 Suggested Activities")
                for tip in suggest_activities(level):
                    st.markdown(f"- {tip}")

                # YouTube Links
                st.subheader("🎥 Helpful Video Resources")
                query = {
                    "low": "relaxing music for stress relief",
                    "medium": "guided meditation for work stress",
                    "high": "motivational speech for depression"
                }[level]
                story_query = f"real success stories overcoming {level} stress"
                st.markdown(f"🎧 **Feel Better Videos** → [Search: *{query}*]({search_youtube_link(query)})")
                st.markdown(f"🌟 **Watch Real Stories** → [Search: *{story_query}*]({search_youtube_link(story_query)})")

                # Story
                st.subheader("🌟 Real Success Story (Inspired by your situation)")
                st.markdown(get_success_story(user_input))

            except Exception as e:
                st.error(f"Error: {str(e)}")

# --- History & Visualization ---
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
