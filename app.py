import streamlit as st
import cohere
import random
from datetime import datetime
import pandas as pd
import os

# --- Config ---
st.set_page_config(page_title="StressEase AI", page_icon="🧘", layout="centered")
co = cohere.Client(st.secrets["api_keys"]["cohere"])

# --- Constants ---
MOODS = ["😌 Calm", "😐 Meh", "😫 Stressed", "😭 Overwhelmed"]
DATA_FILE = "stress_logs.csv"

# --- Theme Colors (match your dark theme)
PRIMARY = "#00d0b3"
BG = "#1e1e2f"
TEXT = "#ffffff"

# --- Styles ---
def section_title(title):
    st.markdown(f"<h3 style='color:{PRIMARY}; margin-top:30px'>{title}</h3>", unsafe_allow_html=True)

def highlight_box(text, icon="💬"):
    st.markdown(
        f"""<div style='background-color:#2c2c3c;padding:15px;border-radius:10px;margin-bottom:15px'>
        <span style='font-size:18px;'>{icon} {text}</span></div>""",
        unsafe_allow_html=True
    )

def card_list(items, icon="⭐"):
    for item in items:
        st.markdown(
            f"""<div style='background-color:#29293d;padding:12px;margin:6px 0;border-radius:8px'>
            <span style='font-size:16px'>{icon} {item}</span></div>""",
            unsafe_allow_html=True
        )

# --- Affirmation of the Day ---
affirmations = [
    "You are doing the best you can. And that’s enough.",
    "Every breath you take is a step toward peace.",
    "You are stronger than you think.",
    "One small step at a time.",
    "Progress, not perfection.",
]
today = datetime.now().day
st.markdown(f"<div style='background-color:#2c2c3c;padding:12px;border-radius:8px'><b>🌞 Daily Affirmation:</b> <i>{affirmations[today % len(affirmations)]}</i></div>", unsafe_allow_html=True)

# --- Inputs ---
st.markdown("### 🧠 Select Your Mood")
mood = st.radio("", MOODS)
user_input = st.text_area("📝 How are you feeling today?", height=150)
journal = st.text_area("📓 Optional journaling (your thoughts, reflections)", height=100)

# --- Cohere Prompt Classification ---
def classify_stress(user_input):
    prompt = f"""Classify the following into: low, medium, or high stress.
Text: "I'm a little anxious but mostly okay" -> low
Text: "Deadlines are crushing and I feel overwhelmed" -> medium
Text: "I feel lost, alone and mentally drained" -> high
Text: "{user_input}" ->"""
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=1,
        temperature=0
    )
    level = response.generations[0].text.strip().lower()
    return level if level in ["low", "medium", "high"] else "medium"

# --- Quote Generator ---
def generate_quotes(level):
    prompt = {
        "low": "Give 2 short light quotes for mild stress.",
        "medium": "Give 2 strong quotes for someone overwhelmed.",
        "high": "Give 2 powerful quotes for emotional burnout."
    }[level]
    response = co.generate(
        model="command-r-plus",
        prompt=prompt,
        max_tokens=100,
        temperature=0.9
    )
    return [q.strip() for q in response.generations[0].text.strip().split("\n") if q.strip()]

# --- Story Generator ---
def generate_story(user_input, religion=None):
    base_prompt = f"""The user said: "{user_input}"\nWrite a 150-word success story of someone with a similar situation. Make it emotional and hopeful."""
    if religion:
        base_prompt += f" Integrate a relevant story from the {religion}."
    response = co.generate(
        model="command-r-plus",
        prompt=base_prompt,
        max_tokens=250,
        temperature=0.7
    )
    return response.generations[0].text.strip()

# --- YouTube Search URL ---
def youtube_search(query):
    return f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

# --- Activity Suggestions ---
def suggest_activities(level):
    if level == "low":
        return ["Take a short nature walk", "Listen to gentle instrumental music"]
    elif level == "medium":
        return ["Do a short breathing meditation", "Try journaling or making a task list"]
    else:
        return ["Call someone you trust", "Try deep breathing or guided therapy videos"]

# --- Log Entry ---
def log_entry(date, mood, level, user_input, journal):
    row = {"date": date, "mood": mood, "stress_level": level, "text": user_input, "journal": journal}
    df = pd.DataFrame([row])
    if os.path.exists(DATA_FILE):
        df.to_csv(DATA_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(DATA_FILE, index=False)

# --- Main Support Button ---
if st.button("💡 Get Personalized Support"):
    if not user_input.strip():
        st.warning("Please describe how you're feeling.")
    else:
        with st.spinner("Analyzing your feelings..."):
            level = classify_stress(user_input)
            st.markdown(f"<h4 style='color:{PRIMARY}'>🧠 Detected Stress Level: <span style='text-transform:uppercase'>{level}</span></h4>", unsafe_allow_html=True)

            log_entry(datetime.now().strftime("%Y-%m-%d"), mood, level, user_input, journal)

            # Quotes
            section_title("💬 Personalized Quotes")
            for quote in generate_quotes(level):
                highlight_box(quote)

            # Activities
            section_title("🧘 Suggested Activities")
            card_list(suggest_activities(level), icon="✅")

            # YouTube Section
            section_title("🎥 Video Resources")
            topic = {
                "low": "relaxing stress relief music",
                "medium": "guided meditation work anxiety",
                "high": "emotional recovery motivation"
            }[level]
            video_link = youtube_search(topic)
            st.markdown(f"🔗 [Explore videos for: *{topic.title()}*]({video_link})", unsafe_allow_html=True)

            # Religion Story (optional: can add dropdown if needed)
            section_title("🌟 Realistic Success Story")
            story = generate_story(user_input)
            st.markdown(
                f"<div style='background-color:#2c2c3c;padding:15px;border-left: 5px solid {PRIMARY};border-radius:10px;'><i>{story}</i></div>",
                unsafe_allow_html=True
            )

# --- Journal History ---
if os.path.exists(DATA_FILE):
    section_title("📈 Mood/Stress Trends")
    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    df["score"] = df["stress_level"].map({"low": 1, "medium": 2, "high": 3})
    st.line_chart(df.groupby("date")["score"].mean())

    with st.expander("📜 See Previous Logs"):
        st.dataframe(df[::-1])


