import os
import re
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

# -----------------------------
# Page setup & styling
# -----------------------------
st.set_page_config(
    page_title="SpyceOfficial — AI Assistant",
    page_icon="🧠",
    layout="wide",
    menu_items={
        "Get Help": "https://docs.streamlit.io/",
        "Report a bug": "https://github.com/streamlit/streamlit/issues",
        "About": "SpyceOfficial — Smart. Clean. No stress."
    }
)

st.markdown("""
<style>
.block-container { padding-top: 2rem; }
.stButton>button { border-radius: 8px; padding: 0.6rem 1rem; font-weight: 600; }
footer { visibility: hidden; }
.brand-title { font-size: 2.0rem; font-weight: 800; letter-spacing: 0.3px; }
.brand-sub { color: #6b7280; }
.card { padding: 1rem; border: 1px solid #e5e7eb; border-radius: 10px; background: #ffffff10; }
.footer-bar { margin-top: 2rem; padding: 0.8rem 1rem; border-top: 1px solid #e5e7eb; display: flex; gap: 0.6rem; align-items: center; flex-wrap: wrap; }
.footer-btn { border: 1px solid #e5e7eb; border-radius: 8px; padding: 0.4rem 0.8rem; text-decoration: none; color: inherit; font-weight: 600; }
.footer-note { color: #6b7280; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Environment & client
# -----------------------------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Missing OPENAI_API_KEY. Add it to your .env file.")
    st.stop()

client = OpenAI(api_key=OPENAI_API_KEY)

BASE_DIR = os.path.abspath(".")
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
os.makedirs(PROJECTS_DIR, exist_ok=True)

# -----------------------------
# Helpers
# -----------------------------
def sanitize_filename(name: str) -> str:
    name = (name or "").strip()
    if not name:
        return "app.py"
    name = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", name)
    if not name.endswith(".py"):
        name += ".py"
    return name

def save_text(content: str, filename: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = sanitize_filename(filename)
    path = os.path.join(PROJECTS_DIR, f"{ts}_{safe}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path

def ask_model(messages, temperature=0.2):
    try:
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=temperature,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {str(e)}"

def init_state():
    if "history" not in st.session_state:
        st.session_state.history = []  # {mode, prompt, filename, path, time}

init_state()

# -----------------------------
# Sidebar — brand, templates, history
# -----------------------------
with st.sidebar:
    st.markdown('<div class="brand-title">🧠 SpyceOfficial</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand-sub">Smart. Clean. No stress.</div>', unsafe_allow_html=True)
    st.divider()

    st.markdown("### 🎯 Quick templates")
    template = st.selectbox(
        "Pick a template to auto-fill the prompt",
        [
            "— None —",
            "Python: Hello World CLI",
            "Python: To-do list (CLI)",
            "Python: Login system (JSON users)",
            "Streamlit: Simple dashboard",
            "Flask: Minimal API with /hello",
        ]
    )

    def template_text(name: str) -> str:
        mapping = {
            "Python: Hello World CLI": "Build a Python CLI that prints 'Hello, SpyceOfficial!'",
            "Python: To-do list (CLI)": "Build a Python CLI to add/list/remove tasks and save them to tasks.json.",
            "Python: Login system (JSON users)": "Build a Python CLI login system with register/login/logout, storing users in users.json (username + hashed password).",
            "Streamlit: Simple dashboard": "Build a Streamlit app with a sidebar, a main chart using random data, and a table view.",
            "Flask: Minimal API with /hello": "Build a Flask app with a /hello endpoint returning JSON {message: 'Hello from SpyceOfficial'}."
        }
        return mapping.get(name, "")

    if template != "— None —":
        st.info("Template selected. It will prefill the prompt in Build mode.")

    st.divider()
    st.markdown("### 📜 History")
    if st.session_state.history:
        for item in reversed(st.session_state.history):
            name = os.path.basename(item.get("path", "")) if item.get("path") else "—"
            st.markdown(
                f"- **Mode:** {item['mode']}  \n"
                f"  **Prompt:** {item['prompt'][:60]}{'...' if len(item['prompt'])>60 else ''}  \n"
                f"  **File:** `{name}` — {item['time']}"
            )
    else:
        st.caption("No items yet. Generate your first result on the right.")

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="brand-title">SpyceOfficial — AI Assistant</div>', unsafe_allow_html=True)
st.caption("Build software, modify code, edit any text, speak to it, or ask anything. Results appear instantly and save neatly.")

# -----------------------------
# Tabs for modes
# -----------------------------
tab_build, tab_modify, tab_edit, tab_ask, tab_voice = st.tabs([
    "🛠️ Build Code",
    "🧩 Modify Code",
    "✍️ Edit Anything",
    "💬 Ask Anything",
    "🎙️ Voice"
])

# -----------------------------
# Build Code
# -----------------------------
with tab_build:
    col_left, col_right = st.columns([2, 1])
    with col_left:
        default_prompt = template_text(template) if template != "— None —" else ""
        prompt = st.text_area(
            "Describe the software to build",
            height=180,
            placeholder="e.g., Build a Python CLI that asks for name and age, then prints a greeting.",
            value=default_prompt
        )
    with col_right:
        filename = st.text_input("File name", value="app.py", help="e.g., app.py, calculator.py")
        st.info("Tip: Files are saved in /projects with a timestamp.")

    generate = st.button("Generate Code", type="primary")

    if generate:
        if not prompt.strip():
            st.warning("Please describe what to build.")
            st.stop()

        with st.spinner("Generating clean code…"):
            messages = [
                {"role": "system", "content": "You are a helpful software engineer. Return only runnable code unless asked otherwise."},
                {"role": "user", "content": prompt}
            ]
            code = ask_model(messages)

        st.subheader("📝 Generated code")
        st.code(code, language="python")

        try:
            path = save_text(code, filename)
            st.success(f"✅ Code saved to {path}")
            st.download_button("Download code file", code, file_name=os.path.basename(path))
            st.session_state.history.append({
                "mode": "Build Code",
                "prompt": prompt,
                "filename": filename,
                "path": path,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            st.error(f"❌ Failed to save file: {str(e)}")

# -----------------------------
# Modify Code
# -----------------------------
with tab_modify:
    col_left, col_right = st.columns([2, 1])
    with col_left:
        base_code = st.text_area(
            "Paste your existing code here",
            height=220,
            placeholder="Paste the code you want to modify."
        )
        change_request = st.text_area(
            "Describe the changes or new features",
            height=140,
            placeholder="e.g., Add login with username/password and save users to a JSON file."
        )
    with col_right:
        filename2 = st.text_input("New file name", value="updated_app.py")
        st.info("Your updated code will be saved in /projects with a timestamp.")

    apply_changes = st.button("Apply Changes", type="primary")

    if apply_changes:
        if not base_code.strip():
            st.warning("Please paste the code to modify.")
            st.stop()
        if not change_request.strip():
            st.warning("Please describe the changes you want.")
            st.stop()

        with st.spinner("Updating your code…"):
            messages = [
                {"role": "system", "content": "You are a senior software engineer. Transform the provided code according to the request. Return only the full updated code."},
                {"role": "user", "content": f"Original code:\n\n{base_code}\n\nChange request:\n{change_request}"}
            ]
            updated = ask_model(messages)

        st.subheader("📝 Updated code")
        st.code(updated, language="python")

        try:
            path = save_text(updated, filename2)
            st.success(f"✅ Updated code saved to {path}")
            st.download_button("Download updated file", updated, file_name=os.path.basename(path))
            st.session_state.history.append({
                "mode": "Modify Code",
                "prompt": change_request,
                "filename": filename2,
                "path": path,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            st.error(f"❌ Failed to save file: {str(e)}")

# -----------------------------
# Edit Anything (text/doc/code)
# -----------------------------
with tab_edit:
    col_left, col_right = st.columns([2, 1])
    with col_left:
        content = st.text_area(
            "Paste any text or code to edit",
            height=220,
            placeholder="Paste an article, email, README, or code."
        )
        edit_request = st.text_area(
            "Describe the edit",
            height=140,
            placeholder="e.g., Rewrite to be more professional and concise. Or: Fix grammar and keep the tone friendly."
        )
    with col_right:
        filename3 = st.text_input("Save edited content as", value="edited.txt")
        st.info("Edits are saved in /projects with a timestamp.")

    apply_edit = st.button("Apply Edit", type="primary")

    if apply_edit:
        if not content.strip():
            st.warning("Please paste the content to edit.")
            st.stop()
        if not edit_request.strip():
            st.warning("Please describe the edit you want.")
            st.stop()

        with st.spinner("Editing…"):
            messages = [
                {"role": "system", "content": "You are a precise editor. Apply the requested changes faithfully. Return only the edited content."},
                {"role": "user", "content": f"Content:\n\n{content}\n\nEdit request:\n{edit_request}"}
            ]
            edited = ask_model(messages)

        st.subheader("📝 Edited content")
        st.code(edited, language="text")

        try:
            path = save_text(edited, filename3)
            st.success(f"✅ Edited content saved to {path}")
            st.download_button("Download edited content", edited, file_name=os.path.basename(path))
            st.session_state.history.append({
                "mode": "Edit Anything",
                "prompt": edit_request,
                "filename": filename3,
                "path": path,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            st.error(f"❌ Failed to save edited content: {str(e)}")

# -----------------------------
# Ask Anything
# -----------------------------
with tab_ask:
    col_left, col_right = st.columns([2, 1])
    with col_left:
        question = st.text_area(
            "Ask anything (facts, time zones, currency, how-to, etc.)",
            height=180,
            placeholder="e.g., What’s the current time in New York and how do I convert 50 USD to EUR?"
        )
    with col_right:
        filename4 = st.text_input("Save answer as (optional)", value="answer.txt")
        st.info("Answers can be saved as text files in /projects.")

    ask = st.button("Get Answer", type="primary")

    if ask:
        if not question.strip():
            st.warning("Please enter your question.")
            st.stop()

        with st.spinner("Thinking…"):
            messages = [
                {"role": "system", "content": "You are a helpful, factual assistant. Provide clear, concise answers. If a calculation depends on live data, explain the method and give an approximate answer."},
                {"role": "user", "content": question}
            ]
            answer = ask_model(messages, temperature=0.0)

        st.subheader("🧠 Answer")
        st.write(answer)

        if filename4.strip():
            try:
                path = save_text(answer, filename4)
                st.success(f"✅ Answer saved to {path}")
                st.download_button("Download answer", answer, file_name=os.path.basename(path))
                st.session_state.history.append({
                    "mode": "Ask Anything",
                    "prompt": question,
                    "filename": filename4,
                    "path": path,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            except Exception as e:
                st.error(f"❌ Failed to save answer: {str(e)}")

# -----------------------------
# Voice (upload audio → transcribe)
# -----------------------------
with tab_voice:
    st.info("Upload a short voice note (WAV/MP3/M4A). I’ll transcribe it and respond.")
    audio_file = st.file_uploader("Upload audio", type=["wav", "mp3", "m4a"])
    filename5 = st.text_input("Save transcript as", value="transcript.txt")
    process_audio = st.button("Transcribe & Answer", type="primary")

    if process_audio:
        if not audio_file:
            st.warning("Please upload an audio file.")
            st.stop()

        with st.spinner("Transcribing…"):
            try:
                temp_path = os.path.join(PROJECTS_DIR, f"temp_{audio_file.name}")
                with open(temp_path, "wb") as f:
                    f.write(audio_file.read())

                audio = open(temp_path, "rb")
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio
                ).text.strip()

                st.subheader("🗣️ Transcript")
                st.write(transcript)

                messages = [
                    {"role": "system", "content": "You are a helpful assistant. Respond clearly and concisely to the user's transcribed voice request."},
                    {"role": "user", "content": transcript}
                ]
                reply = ask_model(messages, temperature=0.2)

                st.subheader("💬 Response")
                st.write(reply)

                combined = f"Transcript:\n{transcript}\n\nResponse:\n{reply}"
                path = save_text(combined, filename5)
                st.success(f"✅ Transcript & response saved to {path}")
                st.download_button("Download transcript & response", combined, file_name=os.path.basename(path))

                st.session_state.history.append({
                    "mode": "Voice",
                    "prompt": transcript,
                    "filename": filename5,
                    "path": path,
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                try:
                    os.remove(temp_path)
                except Exception:
                    pass

            except Exception as e:
                st.error(f"❌ Voice processing failed: {str(e)}")

# -----------------------------
# Footer — polished buttons
# -----------------------------
st.markdown("""
<div class="footer-bar">
  <a class="footer-btn" href="#" target="_self">Home</a>
  <a class="footer-btn" href="#" target="_self">Docs</a>
  <a class="footer-btn" href="#" target="_self">Contact</a>
  <span class="footer-note">Local app. When you’re ready, we’ll deploy to your domain: spyceofficial.com</span>
</div>
""", unsafe_allow_html=True)