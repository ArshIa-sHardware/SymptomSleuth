# SymptomSleuth MVP (Streamlit + ChatGPT Wrapper + PDF generation + Athlete Mode + Emoji Mood + Streaks)
# Run this with: streamlit run app.py

import streamlit as st
from fpdf import FPDF
from datetime import datetime, timedelta 
from openai import OpenAI

# --- Config ---
st.set_page_config(page_title="SymptomSleuth", layout="centered")
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))

# --- App State ---
if "logs" not in st.session_state:
    st.session_state.logs = []
if "last_log_date" not in st.session_state:
    st.session_state.last_log_date = None
if "streak" not in st.session_state:
    st.session_state.streak = 0

# --- Header ---
st.title("🤒 SymptomSleuth")
st.subheader("Track your symptoms. Understand your health.")

# --- Input Form ---
with st.form("log_form"):
    date = st.date_input("Date", value=datetime.today())
    symptoms = st.text_area("Describe your symptoms")

    mood_emoji = st.radio("Mood today", ["😞", "😐", "😊", "😄"], index=2, horizontal=True)

    athlete_mode = st.checkbox("🏃 Athlete Mode: Log body pain")
    pain_areas = []
    if athlete_mode:
        pain_areas = st.multiselect("Select body parts in pain", [
            "Head", "Neck", "Shoulder", "Back", "Elbow", "Wrist",
            "Hip", "Knee", "Ankle", "Foot"
        ])

    submit = st.form_submit_button("Log Entry")

if submit and symptoms.strip():
    # Update streak
    today = date
    if st.session_state.last_log_date:
        diff = (today - st.session_state.last_log_date).days
        if diff == 1:
            st.session_state.streak += 1
        elif diff > 1:
            st.session_state.streak = 1
    else:
        st.session_state.streak = 1

    st.session_state.last_log_date = today

    st.session_state.logs.append({
        "date": date.strftime("%A, %B %d"),
        "symptoms": symptoms.strip(),
        "mood": mood_emoji,
        "pain": pain_areas
    })
    st.success(f"Logged! You're on a {st.session_state.streak}-day streak! 🌟")

# --- Display Logs ---
if st.session_state.logs:
    st.subheader("📝 Your Entries")
    for log in reversed(st.session_state.logs):
        st.markdown(f"**{log['date']}** — Mood: {log['mood']}\n\n{log['symptoms']}")
        if log['pain']:
            st.markdown(f"_Pain Areas_: {', '.join(log['pain'])}")

# --- Generate AI Summary ---
if len(st.session_state.logs) >= 2:
    st.subheader("🧠 AI Weekly Summary")
    if st.button("Generate Summary"):
        entries = "\n".join([
            f"{l['date']}: Mood {l['mood']}. Pain: {', '.join(l['pain']) if l['pain'] else 'None'}. {l['symptoms']}"
            for l in st.session_state.logs
        ])
        prompt = f"""
You are a helpful and professional medical assistant. Analyze the following symptom logs and summarize them clearly for a physician.
Focus on frequency, intensity, emotional trends, body pain, and recurring issues.

Logs:
{entries}

Summarize this in 3 paragraphs.
"""
        with st.spinner("Analyzing logs with ChatGPT..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a compassionate medical assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                summary = response.choices[0].message.content.strip()
                st.text_area("AI Summary", value=summary, height=300)
                st.session_state.last_summary = summary
            except Exception as e:
                st.error("Error: " + str(e))

# --- PDF Export ---
def generate_pdf(summary_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt="SymptomSleuth Report\n\n" + summary_text)
    filename = "symptom_summary.pdf"
    pdf.output(filename)
    return filename

if "last_summary" in st.session_state:
    if st.download_button("📄 Download PDF for Doctor", data=open(generate_pdf(st.session_state.last_summary), "rb").read(), file_name="SymptomSleuth_Report.pdf"):
        st.success("PDF downloaded!")

# --- Footer ---
st.markdown("---")
st.caption("🧠 SymptomSleuth - Created with love by a teen founder for youth wellness. Built with emoji logging, athlete insights, and streak tracking.")
