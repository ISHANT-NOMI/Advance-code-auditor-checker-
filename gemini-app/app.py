import streamlit as st
import requests

# ==========================================
# 1. PAGE CONFIGURATION & STYLING (GLASSMORPHISM)
# ==========================================
st.set_page_config(
    page_title="🕵️‍♀️Advance Code Auditor & Checker",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Classic Glassmorphism CSS
st.markdown('''
    <style>
    /* Global Background: Dark gradient for classic look */
    .stApp {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        color: #ffffff;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Glassmorphism Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Glassmorphism Buttons */
    .stButton>button {
        width: 100%;
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        color: white;
        font-weight: bold;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 12px;
        padding: 12px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover {
        background: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.4);
    }
    
    /* Input Fields (Text Areas, Inputs, Selectboxes) */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div {
        background: rgba(0, 0, 0, 0.2) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 8px;
    }
    
    /* Developer Profile Card - Glass effect */
    .dev-profile {
        text-align: center;
        padding: 20px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-top: 30px;
    }
    .dev-name {
        font-size: 1.4rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-top: 10px;
    }
    .app-title {
        text-align: center;
        font-weight: bold;
        background: linear-gradient(to right, #ffffff, #a8c0ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 30px;
    }
    </style>
''', unsafe_allow_html=True)

# ==========================================
# 2. CORE LOGIC CLASS
# ==========================================
class AdvancedGeminiEngine:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent"

    def fetch_latest_models(self):
        """Fetches valid Gemini models for the provided API key dynamically."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.api_key}"
        try:
            res = requests.get(url, timeout=10)
            if res.status_code == 200:
                data = res.json()
                models = []
                for m in data.get('models', []):
                    # Only include models that can generate content
                    if 'generateContent' in m.get('supportedGenerationMethods', []):
                        name = m.get('name', '').replace('models/', '')
                        models.append(name)
                # Sort to try and put newer ones like '2.5' or 'pro' higher if possible
                models.sort(reverse=True)
                if models:
                    return models
        except Exception:
            pass
        # Robust Fallback list of modern models
        return [
            "gemini-2.5-pro", 
            "gemini-2.5-flash", 
            "gemini-2.0-flash", 
            "gemini-1.5-pro", 
            "gemini-1.5-flash"
        ]

    def process_code(self, code, lang, task, issues=""):
        """Constructs the prompt based on the task (Audit or Fix)."""
        if task == "audit":
            prompt = (
                f"You are a Senior Software Engineer and Code Auditor.\n"
                f"Analyze this {lang} code for bugs, security vulnerabilities, logical errors, and optimization opportunities.\n"
                f"Code:\n```{lang}\n{code.strip()}\n```\n"
                "Provide response in Markdown format:\n"
                "### 🛑 Issues Found (If any)\n"
                "### 💡 Suggestions for Improvement\n"
                "### 📖 Best Practices"
            )
        else:
            prompt = (
                f"You are an Expert Developer.\n"
                f"Fix the following {lang} code based on these known issues:\n{issues}\n"
                f"Original Code:\n```{lang}\n{code.strip()}\n```\n"
                "Provide the COMPLETE, ERROR-FREE, and OPTIMIZED code in a single code block. Include brief inline comments explaining the fixes."
            )
        return prompt

    def execute_request(self, prompt_text, primary_model, candidate_models):
        """Executes API call with automatic fallback if a model fails."""
        queue = [primary_model] + [m for m in candidate_models if m != primary_model]
        last_error = ""

        for model in queue:
            url = self.base_url.format(model) + f"?key={self.api_key}"
            headers = {'Content-Type': 'application/json'}
            payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
            
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    try:
                        text = data['candidates'][0]['content']['parts'][0]['text']
                        return True, model, text
                    except (KeyError, IndexError):
                        return False, model, "API returned an unexpected structure."
                else:
                    last_error = f"HTTP {response.status_code}: {response.text}"
                    # If model not found or access denied, try the next one
                    if response.status_code in [403, 404]:
                        continue
                    elif response.status_code == 400:
                        return False, model, "Invalid API Key or Bad Request."
            except Exception as e:
                last_error = f"Connection Error: {str(e)}"
                continue

        return False, primary_model, f"Request failed across all available models. Last Error: {last_error}"


# ==========================================
# 3. STREAMLIT UI BUILDER
# ==========================================

# --- SIDEBAR: Configuration & Profile ---
st.sidebar.title("⚙️ Setup")
api_key_input = st.sidebar.text_input("🔑 Google Gemini API Key", type="password", help="Get this from Google AI Studio")

# Fetch and display models dynamically based on the key
available_models = ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
if api_key_input:
    engine_temp = AdvancedGeminiEngine(api_key_input)
    fetched = engine_temp.fetch_latest_models()
    if fetched:
        available_models = fetched

selected_model = st.sidebar.selectbox("🤖 Select Latest Model", available_models)

# Developer Profile (Glassmorphism)
st.sidebar.markdown('''
<div class="dev-profile">
    <div style="font-size: 3rem;">👨‍💻</div>
    <div class="dev-name">Ishant Kumar</div>
    <div style="color: #e2e8f0; font-size: 0.85rem; letter-spacing: 1px; margin-top: 5px;">Lead Developer</div>
</div>
''', unsafe_allow_html=True)

# --- MAIN WORKSPACE ---
st.markdown('<h1 class="app-title">Advance Code Auditor & Checker</h1>', unsafe_allow_html=True)

# State setup
if "audit_done" not in st.session_state:
    st.session_state.audit_done = False
if "audit_result" not in st.session_state:
    st.session_state.audit_result = ""
if "source_code" not in st.session_state:
    st.session_state.source_code = ""

col1, col2 = st.columns([1, 3])
with col1:
    LANGUAGE_LIST = ["Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C", "Go", "Rust", "PHP", "Swift", "Kotlin", "SQL", "HTML/CSS"]
    selected_lang = st.selectbox("🌐 Language", LANGUAGE_LIST)

with col2:
    st.info("Paste your code below. Supported across all major languages.")

code_input = st.text_area("💻 Source Code:", height=300, placeholder="Paste your code here...")

# STEP 1: AUDIT
if st.button("🚀 Analyze & Audit Code"):
    if not api_key_input:
        st.error("⚠️ API Key is missing! Please enter your Google Gemini API Key in the sidebar.")
    elif not code_input.strip():
        st.warning("⚠️ Please paste some code to analyze.")
    else:
        with st.spinner(f"Auditing {selected_lang} code..."):
            engine = AdvancedGeminiEngine(api_key_input)
            prompt = engine.process_code(code_input, selected_lang, "audit")
            
            success, used_model, result = engine.execute_request(prompt, selected_model, available_models)
            
            if success:
                st.session_state.audit_result = result
                st.session_state.audit_done = True
                st.session_state.source_code = code_input
                st.session_state.used_model = used_model
                st.rerun()
            else:
                st.error(f"❌ Analysis Failed: {result}")

# STEP 2: REVIEW & FIX
if st.session_state.audit_done:
    st.success(f"✅ Audit completed successfully using **{st.session_state.get('used_model', selected_model)}**")
    
    with st.expander("📊 View Audit Report & Suggestions", expanded=True):
        st.markdown(st.session_state.audit_result)
        
    st.markdown("---")
    st.subheader("🛠️ Auto-Fix & Optimize")
    st.write("Would you like the AI to generate a fixed and optimized version of your code based on the suggestions above?")
    
    if st.button("✨ Generate Error-Free Code"):
        with st.spinner("Writing optimized code..."):
            engine = AdvancedGeminiEngine(api_key_input)
            prompt = engine.process_code(
                st.session_state.source_code, 
                selected_lang, 
                "fix", 
                st.session_state.audit_result
            )
            
            success, used_model, final_code = engine.execute_request(prompt, selected_model, available_models)
            
            if success:
                st.balloons()
                st.success("✅ Code successfully fixed and optimized!")
                st.markdown("### 🏆 Final Output")
                st.markdown(final_code)
            else:
                st.error(f"❌ Auto-Fix Failed: {final_code}")