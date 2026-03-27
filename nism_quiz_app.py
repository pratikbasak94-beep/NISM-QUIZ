import streamlit as st
import google.generativeai as genai
import json
from fpdf import FPDF

# --- 1. PAGE CONFIGURATION & BRANDING ---
st.set_page_config(
    page_title="NISM PREP PORTAL",
    page_icon="🎓",
    layout="wide"
)

# Hide Streamlit Branding (The CSS Assassin)
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- 2. INITIALIZE AI ---
# Pulls the key safely from Streamlit Cloud Secrets or local .streamlit/secrets.toml
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

# --- 3. SESSION STATE MANAGEMENT ---
# Keeps data on screen when buttons are clicked
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "exam_data" not in st.session_state:
    st.session_state.exam_data = None
if "live_notes" not in st.session_state:
    st.session_state.live_notes = None
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

# --- 4. CORE FUNCTIONS ---

def generate_nism_notes(exam, chapter):
    """Generates the study guide."""
    prompt = f"""
    You are an expert Indian financial instructor preparing a student for the SEBI-mandated {exam}.
    Write a comprehensive study guide for '{chapter}'.
    Use clean text, standard bullet points, and short paragraphs. 
    DO NOT use long horizontal lines (like ----) or complex tables. Keep the text simple.
    """
    response = model.generate_content(prompt)
    return response.text

def create_pdf_bytes(text_content):
    """Converts the AI text into a downloadable PDF safely."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("helvetica", size=12)
    
    # Clean text to prevent FPDF crashes (removes emojis and weird markdown lines)
    clean_text = text_content.replace('---', '').replace('***', '')
    safe_text = clean_text.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 8, txt=safe_text)
    # Return raw bytes for Streamlit to download
    return bytes(pdf.output())

def generate_quiz(exam, topic, num_questions):
    """Generates JSON-formatted quizzes."""
    prompt = f"""
    Generate exactly {num_questions} multiple-choice questions for the {exam} certification.
    Focus on: {topic}.
    You MUST respond strictly with a raw, valid JSON array of objects. Do not use Markdown blocks (like ```json).
    Each object must have exactly these keys:
    "question": the question text,
    "options": an array of 4 string options,
    "answer": the exact string of the correct option,
    "explanation": a short explanation.
    """
    response = model.generate_content(prompt)
    try:
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_json)
    except Exception as e:
        st.error("AI formatting error. Please try generating again.")
        return None

# --- 5. SIDEBAR NAVIGATION ---
st.sidebar.title("🎓 NISM PREP PORTAL")
st.sidebar.markdown("### Select Study Mode")
app_mode = st.sidebar.radio("Navigation", ["📖 Live Notes & PDF", "📝 10-Question Quiz", "🏆 30-Mark Full Exam"])

st.sidebar.divider()
exam_choice = st.sidebar.selectbox("Certification:", ["NISM Series V-A: Mutual Fund Distributors"])

chapters_va = [
    "Chapter 1: Investment Landscape",
    "Chapter 2: Concept and Role of a Mutual Fund",
    "Chapter 3: Legal Structure of Mutual Funds in India",
    "Chapter 4: Legal and Regulatory Framework",
    "Chapter 5: Scheme Related Information Documents"
]

# --- 6. MAIN UI ROUTING ---

# MODE 1: LIVE NOTES & PDF DOWNLOAD
if app_mode == "📖 Live Notes & PDF":
    st.title("📖 Accelerated Live Notes")
    chapter_choice = st.selectbox("Select Chapter:", chapters_va)
    
    if st.button("Generate Notes & PDF"):
        with st.spinner("AI is writing your notes and compiling the PDF..."):
            notes_text = generate_nism_notes(exam_choice, chapter_choice)
            st.session_state.live_notes = notes_text
            st.session_state.pdf_bytes = create_pdf_bytes(notes_text)
            st.rerun()

    # Display Notes and Download Button if they exist
    if st.session_state.live_notes and st.session_state.pdf_bytes:
        st.success("✅ Notes Generated Successfully!")
        
        st.download_button(
            label="📥 Download Notes as PDF",
            data=st.session_state.pdf_bytes,
            file_name=f"{chapter_choice.replace(' ', '_')}_Notes.pdf",
            mime="application/pdf",
            type="primary"
        )
        st.divider()
        st.markdown(st.session_state.live_notes)


# MODE 2: 10-QUESTION QUIZ
elif app_mode == "📝 10-Question Quiz":
    st.title("📝 Chapter Practice Quiz")
    chapter_choice = st.selectbox("Select Chapter to Test:", chapters_va)
    
    if st.button("Generate 10 Questions"):
        with st.spinner("AI is compiling your quiz..."):
            st.session_state.quiz_data = generate_quiz(exam_choice, chapter_choice, 10)
            st.rerun()

    if st.session_state.quiz_data:
        st.subheader(f"Quiz: {chapter_choice}")
        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                user_answers[i] = st.radio("Options", q['options'], key=f"q_{i}", label_visibility="collapsed")
                st.write("") 
            
            if st.form_submit_button("Submit Answers"):
                score = 0
                st.divider()
                st.subheader("Quiz Results")
                for i, q in enumerate(st.session_state.quiz_data):
                    if user_answers[i] == q['answer']:
                        score += 1
                        st.success(f"**Q{i+1}: Correct!** {q['explanation']}")
                    else:
                        st.error(f"**Q{i+1}: Incorrect.** Correct Answer: {q['answer']} | {q['explanation']}")
                st.metric(label="Final Score", value=f"{score} / 10")


# MODE 3: 30-MARK PREMIUM EXAM
elif app_mode == "🏆 30-Mark Full Exam":
    st.title("🏆 The Ultimate 30-Mark Boss Exam")
    st.info("Dynamically generates a unique, high-difficulty test spanning the entire syllabus.")
    
    if st.button("Start AI Mock Exam"):
        with st.spinner("AI is building your unique 30-mark test..."):
            st.session_state.exam_data = generate_quiz(exam_choice, "Entire NISM V-A Syllabus, high difficulty", 30)
            st.rerun()

    if st.session_state.exam_data:
        st.subheader("Full Mock Examination")
        with st.form("exam_form"):
            user_exam_answers = {}
            for i, q in enumerate(st.session_state.exam_data):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                user_exam_answers[i] = st.radio("Options", q['options'], key=f"exam_q_{i}", label_visibility="collapsed")
                st.write("")
            
            if st.form_submit_button("Submit Exam"):
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
