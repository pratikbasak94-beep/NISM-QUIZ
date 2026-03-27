import streamlit as st
import google.generativeai as genai
import json
from fpdf import FPDF

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="NISM PREP PORTAL", page_icon="🎓", layout="wide")

# Hide Streamlit Branding
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# --- 2. SIDEBAR: SETTINGS & NAVIGATION ---
st.sidebar.title("🛠️ Control Panel")

# API KEY INPUT
user_api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password", help="Get yours at aistudio.google.com")

# UPGRADED: NEXT-GEN AI MODEL SELECTOR
model_choice = st.sidebar.selectbox(
    "Select AI Engine:", 
    ["1. Gemini 2.0 Flash Lite (Fastest)", "2. Gemini 2.5 Flash (Balanced)", "3. Gemini 2.5 Pro (Heavy/Fallback)"],
    help="Start with 2.0 Flash Lite. Switch to 2.5 Pro for highly complex JSON quiz generation."
)

# Map the dropdown choices to the actual 2.x API backend strings
model_map = {
    "1. Gemini 2.0 Flash Lite (Fastest)": "gemini-2.0-flash-lite", 
    "2. Gemini 2.5 Flash (Balanced)": "gemini-2.5-flash",
    "3. Gemini 2.5 Pro (Heavy/Fallback)": "gemini-2.5-pro"
}
active_model_string = model_map[model_choice]

st.sidebar.divider()

# NAVIGATION
app_mode = st.sidebar.radio("Go To:", ["📖 Study Notes & PDF", "📝 Chapter Quiz", "🏆 30-Mark Exam"])

st.sidebar.divider()

# SYLLABUS DATA
full_chapters_va = [
    "Chapter 1: Investment Landscape", "Chapter 2: Concept and Role of a Mutual Fund",
    "Chapter 3: Legal Structure of Mutual Funds in India", "Chapter 4: Legal and Regulatory Framework",
    "Chapter 5: Scheme Related Information Documents", "Chapter 6: Fund Administration and Services",
    "Chapter 7: Net Asset Value, Total Expense Ratio and Pricing of Units",
    "Chapter 8: Taxation, Adverse Selection and Prevention of Money Laundering",
    "Chapter 9: Mutual Fund Products", "Chapter 10: Investment Management",
    "Chapter 11: Helping Investors with Financial Planning", "Chapter 12: Helping Investors with Mutual Funds",
    "Chapter 13: Recommending Suitable Schemes to Investors"
]

# --- 3. SESSION STATE ---
if "live_notes" not in st.session_state: st.session_state.live_notes = None
if "pdf_bytes" not in st.session_state: st.session_state.pdf_bytes = None
if "quiz_data" not in st.session_state: st.session_state.quiz_data = None
if "exam_data" not in st.session_state: st.session_state.exam_data = None

# --- 4. CORE ENGINE (AI & PDF) ---

def get_ai_response(prompt, model_name):
    """Generates AI content using the dynamically selected Next-Gen model."""
    if not user_api_key:
        st.error("⚠️ Please enter your API Key in the sidebar first!")
        return None
    try:
        genai.configure(api_key=user_api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"❌ AI Error: {e}")
        return None

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_font("helvetica", size=12)
    safe_text = text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 8, txt=safe_text)
    return bytes(pdf.output())

# --- 5. MAIN INTERFACE ---

st.title("🎓 NISM PREP PORTAL")

# MODE 1: STUDY Notes & PDF
if app_mode == "📖 Study Notes & PDF":
    st.subheader("Interactive Study Material")
    chapter = st.selectbox("Select Chapter:", full_chapters_va)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Generate Notes", use_container_width=True):
            with st.spinner(f"Drafting notes using {model_choice.split('(')[0].strip()}..."):
                prompt = f"Write detailed NISM Series V-A exam notes for {chapter}. Focus on SEBI regulations, definitions, and key concepts. Use clear headings and bullet points. Do not use complex tables or special markdown dividers."
                st.session_state.live_notes = get_ai_response(prompt, active_model_string)
                st.session_state.pdf_bytes = None
    
    with col2:
        if st.session_state.live_notes:
            if st.button("📄 Prepare Downloadable PDF", use_container_width=True):
                st.session_state.pdf_bytes = create_pdf(st.session_state.live_notes)
                st.success("PDF Ready!")

    if st.session_state.pdf_bytes:
        st.download_button("📥 Download PDF Now", st.session_state.pdf_bytes, f"{chapter}.pdf", "application/pdf", use_container_width=True)

    if st.session_state.live_notes:
        st.divider()
        st.markdown(st.session_state.live_notes)

# MODE 2: CHAPTER QUIZ
elif app_mode == "📝 Chapter Quiz":
    st.subheader("10-Question Knowledge Check")
    quiz_ch = st.selectbox("Topic:", full_chapters_va)
    
    if st.button("Generate Quiz", use_container_width=True):
        with st.spinner(f"Creating MCQs using {model_choice.split('(')[0].strip()}..."):
            prompt = f"Generate 10 MCQs for NISM V-A on {quiz_ch} in RAW JSON format. Keys must be exactly: question, options (list of 4 strings), answer (correct string), explanation."
            raw_json = get_ai_response(prompt, active_model_string)
            if raw_json:
                try:
                    st.session_state.quiz_data = json.loads(raw_json.replace("```json", "").replace("```", "").strip())
                except json.JSONDecodeError:
                    st.error(f"The AI returned badly formatted JSON. Try generating again, or switch to Gemini 2.5 Pro in the sidebar for stricter formatting.")

    if st.session_state.quiz_data:
        with st.form("quiz_form"):
            u_ans = {}
            for i, q in enumerate(st.session_state.quiz_data):
                st.write(f"**Q{i+1}: {q['question']}**")
                u_ans[i] = st.radio("Options", q['options'], key=f"q{i}", label_visibility="collapsed")
            if st.form_submit_button("Submit"):
                score = sum([1 for i, q in enumerate(st.session_state.quiz_data) if u_ans[i] == q['answer']])
                st.metric("Score", f"{score}/10")
                for i, q in enumerate(st.session_state.quiz_data):
                    if u_ans[i] == q['answer']: st.success(f"Q{i+1}: Correct! {q['explanation']}")
                    else: st.error(f"Q{i+1}: Wrong. Answer: {q['answer']}. {q['explanation']}")

# MODE 3: 30-MARK EXAM
elif app_mode == "🏆 30-Mark Exam":
    st.subheader("Full Mock Simulation")
    if st.button("Generate 30-Mark Exam", use_container_width=True):
        with st.spinner(f"Building final exam using {model_choice.split('(')[0].strip()}..."):
            prompt = f"Generate 30 difficult MCQs for NISM Series V-A Full Syllabus in RAW JSON format. Keys: question, options, answer, explanation."
            raw_ex = get_ai_response(prompt, active_model_string)
            if raw_ex:
                try:
                    st.session_state.exam_data = json.loads(raw_ex.replace("```json", "").replace("```", "").strip())
                except json.JSONDecodeError:
                    st.error("JSON formatting error. Please try again or switch the model to Gemini 2.5 Pro.")

    if st.session_state.exam_data:
        with st.form("exam_form"):
            e_ans = {}
            for i, q in enumerate(st.session_state.exam_data):
                st.write(f"**Q{i+1}: {q['question']}**")
                e_ans[i] = st.radio("Options", q['options'], key=f"ex{i}", label_visibility="collapsed")
            if st.form_submit_button("Finish Exam"):
                final_score = sum([1 for i, q in enumerate(st.session_state.exam_data) if e_ans[i] == q['answer']])
                st.metric("Final Result", f"{final_score}/30")
                if final_score >= 15: st.success("🎉 You Passed!")
                else: st.warning("📚 More practice needed.")
