import streamlit as st
import google.generativeai as genai
import json

# --- 1. PAGE CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="NISM PREP PORTAL",
    page_icon="🎓",
    layout="wide"
)

# Hide Streamlit Branding for a clean SaaS look
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. INITIALIZE AI ---
# Assumes you have .streamlit/secrets.toml with GEMINI_API_KEY
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. SESSION STATE MANAGEMENT ---
# This keeps our generated quizzes on the screen while we answer them
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "exam_data" not in st.session_state:
    st.session_state.exam_data = None

# --- 4. AI GENERATION FUNCTIONS ---
def generate_nism_notes(exam, chapter):
    prompt = f"""
    You are an expert Indian financial instructor preparing a student for the SEBI-mandated {exam} certification.
    Write a comprehensive, highly accurate study guide for '{chapter}'.
    Format the output strictly in Markdown with clean headings, bullet points, and bold text for key terms.
    Ensure all taxation, mutual fund regulations, and compliance rules are accurate to current Indian standards.
    """
    response = model.generate_content(prompt)
    return response.text

def generate_quiz(exam, topic, num_questions):
    prompt = f"""
    Generate exactly {num_questions} multiple-choice questions for the {exam} certification.
    Focus on: {topic}.
    You MUST respond strictly with a raw, valid JSON array of objects. Do not use Markdown blocks (like ```json).
    Each object must have exactly these keys:
    "question": the question text,
    "options": an array of 4 string options,
    "answer": the exact string of the correct option,
    "explanation": a short explanation of why it is correct.
    """
    response = model.generate_content(prompt)
    try:
        # Strip out markdown formatting if the AI accidentally includes it
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        st.error("Failed to parse AI response. Please try generating again.")
        return None

# --- 5. SIDEBAR NAVIGATION ---
st.sidebar.title("🎓 NISM PREP PORTAL")
st.sidebar.markdown("### Select Study Mode")
app_mode = st.sidebar.radio("Navigation", ["📖 Live Notes", "📝 10-Question Quiz", "🏆 30-Mark Full Exam"])

st.sidebar.divider()
exam_choice = st.sidebar.selectbox("Certification:", ["NISM Series V-A: Mutual Fund Distributors"])

chapters_va = [
    "Chapter 1: Investment Landscape",
    "Chapter 2: Concept and Role of a Mutual Fund",
    "Chapter 3: Legal Structure of Mutual Funds in India",
    "Chapter 4: Legal and Regulatory Framework",
    "Chapter 5: Scheme Related Information Documents"
]

# --- 6. MAIN UI LOGIC ---

# MODE 1: LIVE NOTES
if app_mode == "📖 Live Notes":
    st.title("📖 Accelerated Live Notes")
    chapter_choice = st.selectbox("Select Chapter:", chapters_va)
    
    if st.button("Generate Notes"):
        with st.spinner("AI is analyzing the syllabus and writing your notes..."):
            live_notes = generate_nism_notes(exam_choice, chapter_choice)
            st.success(f"Notes for {chapter_choice} generated successfully!")
            st.markdown(live_notes)

# MODE 2: 10-QUESTION QUIZ
elif app_mode == "📝 10-Question Quiz":
    st.title("📝 Chapter Practice Quiz")
    chapter_choice = st.selectbox("Select Chapter to Test:", chapters_va)
    
    if st.button("Generate 10 Questions"):
        with st.spinner("AI is compiling your quiz..."):
            st.session_state.quiz_data = generate_quiz(exam_choice, chapter_choice, 10)
            st.rerun() # Refresh the page to show the quiz

    # If quiz data exists in memory, display the interactive form
    if st.session_state.quiz_data:
        st.subheader(f"Quiz: {chapter_choice}")
        
        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                user_answers[i] = st.radio("Options", q['options'], key=f"q_{i}", label_visibility="collapsed")
                st.write("") 
            
            submitted = st.form_submit_button("Submit Answers")
            
            if submitted:
                score = 0
                st.divider()
                st.subheader("Quiz Results")
                for i, q in enumerate(st.session_state.quiz_data):
                    if user_answers[i] == q['answer']:
                        score += 1
                        st.success(f"**Q{i+1}: Correct!** {q['explanation']}")
                    else:
                        st.error(f"**Q{i+1}: Incorrect.** The correct answer was: {q['answer']}. {q['explanation']}")
                
                st.metric(label="Final Score", value=f"{score} / 10")

# MODE 3: 30-MARK PREMIUM EXAM
elif app_mode == "🏆 30-Mark Full Exam":
    st.title("🏆 The Ultimate 30-Mark Boss Exam")
    st.info("This exam pulls from the entire syllabus. It will dynamically generate a unique, high-difficulty test every single time.")
    
    if st.button("Start AI Mock Exam"):
        with st.spinner("AI is generating your unique 30-mark test. This may take a few seconds..."):
            # We ask the AI to test the whole syllabus
            st.session_state.exam_data = generate_quiz(exam_choice, "Entire NISM V-A Syllabus, high difficulty", 30)
            st.rerun()

    # Display the 30-mark interactive form
    if st.session_state.exam_data:
        st.subheader("Full Mock Examination")
        
        with st.form("exam_form"):
            user_exam_answers = {}
            for i, q in enumerate(st.session_state.exam_data):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                user_exam_answers[i] = st.radio("Options", q['options'], key=f"exam_q_{i}", label_visibility="collapsed")
                st.write("")
            
            exam_submitted = st.form_submit_button("Submit Exam")
            
            if exam_submitted:
                exam_score = 0
                st.divider()
                st.subheader("Exam Results")
                for i, q in enumerate(st.session_state.exam_data):
                    if user_exam_answers[i] == q['answer']:
                        exam_score += 1
                    else:
                        st.error(f"**Q{i+1}: Incorrect.** Answer: {q['answer']} | {q['explanation']}")
                
                st.metric(label="Final Exam Score", value=f"{exam_score} / 30")
                if exam_score >= 15:
                    st.success("✅ Passing Grade Achieved! You are ready for the real thing.")
                else:
                    st.warning("⚠️ Below Passing Grade. Review your live notes and try again.")
