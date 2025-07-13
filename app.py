import streamlit as st
import cohere
import random
from datetime import datetime
import pandas as pd
import os

# --- Custom Style ---
st.markdown("""
<style>
body {
    background: linear-gradient(to bottom, #1e1e2f, #2c2c3c);
}
.main {
    background-color: rgba(30,30,47,0.95);
}
section {
    margin-bottom: 30px;
}
.quote-box, .activity-box, .story-box {
    background-color: #2c2c3c;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

# --- Config ---
st.set_page_config(page_title="Stress Management AI", page_icon="🧘", layout="centered")
st.title("🧠 Stress Management Assistant")
st.markdown("Track your feelings and receive personalized emotional and spiritual support.")

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
    "One small step at a time.",
    "Progress, not perfection.",
]
st.info(f"🌞 Daily Affirmation: *{affirmations[datetime.now().day % len(affirmations)]}*")

# --- User Inputs ---
mood = st.radio("🧠 How are you feeling today?", MOODS)
spiritual_choice = st.selectbox("📖 Do you want your support to include spiritual insight from:", SPIRITUAL_BOOKS)
user_input = st.text_area("📝 Describe your current stress or thoughts:", height=150)
journal = st.text_area("📓 Optional journaling space:", height=100)

# --- Stress Classification ---
def classify_stress(user_input):
    prompt = f"""Classify the following into low, medium, or high stress.

Text: "I'm a little anxious but mostly okay" → low  
Text: "Deadlines are crushing me" → medium  
Text: "I feel mentally drained and hopeless" → high  
Text: "{user_input}" →"""

    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=1,
        temperature=0
    )
    level = response.generations[0].text.strip().lower()
    return level if level in ["low", "medium", "high"] else "medium"

# --- Quotes ---
def generate_quotes(level):
    prompts = {
        "low": "Give 2 light motivational quotes for someone slightly stressed.",
        "medium": "Give 2 strong motivational quotes for someone overwhelmed.",
        "high": "Give 2 powerful quotes for someone facing deep emotional stress."
    }
    prompt = prompts[level]
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=100,
        temperature=0.9,
    )
    return [q.strip("- ") for q in response.generations[0].text.strip().split("\n") if q.strip()]

# --- Activities ---
def suggest_activities(level):
    if level == "low":
        return [
            ("🌳 Take a short walk", "Walking helps release endorphins and refresh the mind."),
            ("🎧 Listen to soft music", "Music can reduce cortisol and improve mood.")
        ]
    elif level == "medium":
        return [
            ("🧘 Practice 5-minute meditation", "Helps reduce anxiety and improve emotional balance."),
            ("📋 Break down your tasks", "Avoid overwhelm by organizing your thoughts.")
        ]
    else:
        return [
            ("📞 Speak to a friend or therapist", "Social support is essential during emotional burnout."),
            ("✍️ Reflect by journaling", "Writing helps process emotions and release inner tension.")
        ]

# --- Success Story ---
def get_success_story(user_input, spiritual_choice):
    prompt = f"""
Someone feels: "{user_input}"

Write a 150-word emotionally comforting success story. 
Mention how they healed step-by-step and end with a peaceful thought.
Include a quote or story from {spiritual_choice if spiritual_choice != 'None' else 'a wise thinker'} if applicable.
Do not say it’s fictional or AI-generated.
"""
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=300,
        temperature=0.8,
    )
    return response.generations[0].text.strip()

# --- YouTube Links ---
def youtube_search_link(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- Log Entry ---
def log_entry(date, mood, level, user_input, journal):
    row = {"date": date, "mood": mood, "stress_level": level, "text": user_input, "journal": journal}
    df = pd.DataFrame([row])
    if os.path.exists(DATA_FILE):
        df.to_csv(DATA_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(DATA_FILE, index=False)

# --- Support Engine ---
if st.button("💡 Get Support"):
    if not user_input.strip():
        st.warning("Please describe your current state.")
    else:
        with st.spinner("Analyzing your emotions..."):
            level = classify_stress(user_input)
            st.success(f"🧠 Detected Stress Level: **{level.upper()}**")
            log_entry(datetime.now().strftime("%Y-%m-%d"), mood, level, user_input, journal)

            # --- Quotes ---
            st.markdown("### 💬 Motivational Quotes")
            for quote in generate_quotes(level):
                st.markdown(f"<div class='quote-box'>💬 {quote}</div>", unsafe_allow_html=True)

            # --- Activities ---
            st.markdown("### 💡 Activities & Why They Help")
            for act, reason in suggest_activities(level):
                st.markdown(f"<div class='activity-box'><b>{act}</b><br><span style='font-size:13px'>{reason}</span></div>", unsafe_allow_html=True)

            # --- Success Story ---
            st.markdown("### 🌟 A Story to Inspire You")
            st.markdown(f"<div class='story-box'>{get_success_story(user_input, spiritual_choice)}</div>", unsafe_allow_html=True)

            # --- YouTube Video Search ---
            st.markdown("### 🎥 Explore Uplifting Videos")
            queries = {
                "low": "relaxing nature sounds",
                "medium": "guided meditation for stress",
                "high": "real depression recovery stories"
            }
            st.markdown(f"🔗 [🎧 Music/Meditation → {queries[level].title()}]({youtube_search_link(queries[level])})")
            st.markdown(f"🔗 [🌟 Success Stories Videos]({youtube_search_link('success stories about ' + level + ' stress')})")
            if spiritual_choice != "None":
                st.markdown(f"🔗 [📖 {spiritual_choice} Inspiration Videos]({youtube_search_link(spiritual_choice + ' stress relief')})")

# --- Journal History ---
if os.path.exists(DATA_FILE):
    st.markdown("---")
    st.markdown("### 📊 Your Emotional Trends")
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df["score"] = df["stress_level"].map({"low": 1, "medium": 2, "high": 3})
    chart_data = df.groupby("date")["score"].mean()
    st.line_chart(chart_data)

    with st.expander("📔 View Journal Log"):
        st.dataframe(df[::-1])



