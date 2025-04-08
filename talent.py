import openai
import streamlit as st
import os
import json
import requests
from datetime import datetime

# Firebase config
FIREBASE_URL = "https://talent-scout-path-to-firebase"
CANDIDATES_PATH = "/candidates.json"
EMPLOYERS_PATH = "/employers.json"

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY", "Your Api Key")

# Save candidate data
def save_candidate_to_firebase(data):
    try:
        response = requests.post(FIREBASE_URL + CANDIDATES_PATH, json=data)
        return response.status_code == 200
    except Exception as e:
        return False

# Get candidates
def get_all_candidates():
    try:
        response = requests.get(FIREBASE_URL + CANDIDATES_PATH)
        return response.json() if response.status_code == 200 else {}
    except:
        return {}

# Check employer credentials
def validate_employer_login(username, password):
    try:
        response = requests.get(FIREBASE_URL + EMPLOYERS_PATH)
        if response.status_code == 200:
            employers = response.json()
            for _, user in employers.items():
                if user.get("username") == username and user.get("password") == password:
                    return True
    except:
        pass
    return False

# Evaluate using GPT
def evaluate_responses(tech_stack, answers):
    prompt = f"""
    You are a senior technical recruiter. Based on the candidate's answers below, provide a brief evaluation.
    Tech Stack: {tech_stack}
    Answers: {answers}
    Respond with a concise evaluation in 2-3 sentences.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a senior technical recruiter evaluating candidate responses."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()

# Streamlit UI
def main():
    st.set_page_config(page_title="TalentScout AI Hiring Assistant", layout="wide")
    st.title("🤖 TalentScout - AI Hiring Assistant")

    tabs = st.tabs(["👨‍💻 Interview Bot", "🔐 Employer Login"])

    with tabs[0]:
        system_prompt = """
        You are an AI-powered hiring assistant for TalentScout. Your job is to:
        1. Ask the candidate's name.
        2. Ask for email and years of experience.
        3. Ask about their primary tech stack.
        4. Ask 2-3 technical questions based on that stack.
        5. Thank them and say a recruiter will be in touch.
        """

        if st.button("🔄 Reset Session"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "system", "content": system_prompt},
                {"role": "assistant", "content": "Hi! I'm TalentScout. Can we start with your full name?"}
            ]

        if "answers" not in st.session_state:
            st.session_state.answers = ""
            st.session_state.name = ""
            st.session_state.email = ""
            st.session_state.experience = None
            st.session_state.tech_stack = ""
            st.session_state.resume_filename = ""
            st.session_state.saved_to_firebase = False

        uploaded_file = st.file_uploader("📎 Upload your resume", type=["pdf", "docx"])
        if uploaded_file:
            resume_path = os.path.join("resumes", uploaded_file.name)
            os.makedirs("resumes", exist_ok=True)
            with open(resume_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.resume_filename = uploaded_file.name

        user_input = st.chat_input("Your response")
        if user_input:
            last_question = next((msg["content"] for msg in reversed(st.session_state.messages) if msg["role"] == "assistant"), "")
            st.session_state.answers += f"Q: {last_question}\nA: {user_input}\n"
            st.session_state.messages.append({"role": "user", "content": user_input})

            if not st.session_state.name:
                st.session_state.name = user_input
            elif not st.session_state.email and "@" in user_input:
                st.session_state.email = user_input
            elif st.session_state.experience is None:
                st.session_state.experience = next((int(w) for w in user_input.split() if w.isdigit()), None)
            elif not st.session_state.tech_stack:
                st.session_state.tech_stack = user_input

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=st.session_state.messages,
                temperature=0.7
            )
            reply = response.choices[0].message.content
            st.session_state.messages.append({"role": "assistant", "content": reply})

        for msg in st.session_state.messages:
            if msg["role"] != "system":
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if (
            not st.session_state.get("saved_to_firebase") and
            all([
                st.session_state.name,
                st.session_state.email,
                st.session_state.experience is not None,
                st.session_state.tech_stack
            ])
        ):
            last_reply = st.session_state.messages[-1]["content"].lower()
            if "recruiter will be in touch" in last_reply or "thank you" in last_reply:
                eval_text = evaluate_responses(st.session_state.tech_stack, st.session_state.answers)
                candidate_data = {
                    "name": st.session_state.name,
                    "email": st.session_state.email,
                    "experience": st.session_state.experience,
                    "tech_stack": st.session_state.tech_stack,
                    "responses": st.session_state.answers,
                    "evaluation": eval_text,
                    "timestamp": datetime.now().isoformat(),
                    "resume_filename": st.session_state.resume_filename
                }
                success = save_candidate_to_firebase(candidate_data)
                st.session_state.saved_to_firebase = success
                if success:
                    st.success("✅ Candidate data saved to Firebase and evaluated.")
                else:
                    st.error("❌ Failed to save candidate data.")

    with tabs[1]:
        st.subheader("🔐 Employer Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if "employer_logged_in" not in st.session_state:
            st.session_state["employer_logged_in"] = False

        if st.button("Login"):
            if validate_employer_login(username, password):
                st.session_state["employer_logged_in"] = True
                st.success("✅ Login successful")
            else:
                st.session_state["employer_logged_in"] = False
                st.error("❌ Invalid credentials.")

        if st.session_state.get("employer_logged_in"):
            st.subheader("📋 Candidate Dashboard")

            filter_tech = st.text_input("🔍 Filter by Tech Stack")
            min_exp = st.slider("📊 Minimum Experience (Years)", 0, 20, 0)

            candidates = get_all_candidates()
            if not candidates:
                st.info("No candidate data found.")

            filtered_candidates = [c for _, c in candidates.items()
                                   if (filter_tech.lower() in c['tech_stack'].lower()) and (c['experience'] >= min_exp)]

            for c in sorted(filtered_candidates, key=lambda x: x['timestamp'], reverse=True):
                with st.expander(f"👤 {c['name']} ({c['email']}) - {c['experience']} yrs"):
                    st.markdown(f"**Tech Stack:** {c['tech_stack']}")
                    st.markdown(f"**Evaluation:** {c['evaluation']}")
                    st.markdown(f"**Timestamp:** {c['timestamp']}")
                    if c.get("resume_filename"):
                        resume_path = os.path.join("resumes", c['resume_filename'])
                        if os.path.exists(resume_path):
                            with open(resume_path, "rb") as f:
                                unique_key = f"download_{c['email']}_{c['timestamp']}"
                                st.download_button("📄 Download Resume", f, file_name=c['resume_filename'], key=unique_key)

if __name__ == "__main__":
    main()