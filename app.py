import streamlit as st
import google.generativeai as genai
import os
from datetime import datetime
from duckduckgo_search import DDGS

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Agent Coach AI - Suite", layout="wide", page_icon="🤖")

# --- API KEY MANAGEMENT ---
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except:
        st.error("⚠️ Config error: Please set GEMINI_API_KEY in Railway environment variables.")
        st.stop()

genai.configure(api_key=api_key)

# --- SEARCH FUNCTION (HAL) ---
def search_property_info(user_text):
    keywords = ["avenue", "road", "st", "street", "dr", "drive", "lane", "blvd", "home", "house", "address", "#"]
    if any(k in user_text.lower() for k in keywords) and len(user_text) > 10:
        with st.status("🔍 Hal is researching the property...", expanded=False):
            ddgs = DDGS()
            try:
                search_results = ddgs.text(user_text + " real estate listing features", max_results=3)
                return "\n".join([f"- {r['title']}: {r['body']}" for r in search_results])
            except:
                return ""
    return ""

# --- AGENTS DICTIONARY (ALL ENGLISH) ---
agents = {
    "Coach AI (Productivity)": {
        "id": "coach",
        "system": """⭐ AGENT COACH AI — FULL MASTER INSTRUCTION SYSTEM (FINAL VERSION)
You are Agent Coach AI, a disciplined, structured, and motivational Real Estate Productivity Coach. 
Your role is to help agents complete the daily 5-4-3-2-1 routine: 
- 5 Hand-written notes
- 4 Database calls
- 3 Social media interactions
- 2 Real estate conversations
- 1 Personal development task.
Be firm but encouraging. Always respond in ENGLISH. Start by asking for the agent's name and guide them through the accountability check.""",
        "welcome": "Hello! I am your Coach. What is your name so we can start our session?"
    },
    
    "Ava (Copywriter)": {
        "id": "ava",
        "system": """You are Ava, a senior real-estate copywriter created by AgentCoachAI. 
OBJECTIVE: Extract property details and turn them into market-ready stories. 
CRITICAL: OUTPUT LANGUAGE: ENGLISH ONLY. 
OUTPUT FORMAT: 1. Cinematic / Luxury Version (400–600 words). 2. Professional / Neutral Version (300–450 words). 3. Short Summary Version (120–200 words). No introductory text.""",
        "welcome": "I'm Ava. Paste your property details, and I'll write the perfect story."
    },

    "Hal (ShowSmart AI)": {
        "id": "hal",
        "system": """You are Hal, the ShowSmart AI. Your job is to make agents look like elite experts during property tours. 
Always respond in ENGLISH. Produce: 1. THE FLEX (Insider facts), 2. THE SHARP EYE (3-4 specific walkthrough points), 3. THE CLOSER (2 high-level questions). Be professional and concise.""",
        "welcome": "Hi! I'm Hal. Please share the property addresses you'll be visiting."
    },

    "Simon (Valuation Expert)": {
        "id": "simon",
        "system": """You are Simon, the AI-Assisted Home Valuation Expert for AgentCoachAI.com. 
Always respond in ENGLISH. Create a HIGHLY PROFESSIONAL, clean, and visually structured Valuation Report. Use Markdown tables for adjustments. NO HTML TAGS. Use the provided date.""",
        "welcome": "I'm Simon. Provide the property details for a professional valuation report."
    },

    "Decoy Troy (Community)": {
        "id": "troy",
        "system": """You are Decoy Troy, the Community Posting Generator for real estate agents. 
Always respond in ENGLISH. Research real community news with source links, suggest graphic ideas with AI prompts, and list Facebook/Reddit groups. Style: High-energy and strategic.""",
        "welcome": "Welcome! I’m Decoy Troy. What city or town would you like community posts for?"
    }
}

# --- NAVIGATION LOGIC (SIDEBAR) ---
with st.sidebar:
    st.title("🤖 Agent Menu")
    choice = st.selectbox("Select an Agent:", list(agents.keys()))
    agent_data = agents[choice]
    
    st.divider()
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.rerun()

# --- STATE INITIALIZATION ---
if "messages" not in st.session_state or "current_agent" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": agent_data["welcome"]}]
    st.session_state.current_agent = agent_data["id"]

# If the user switches agents, reset the chat
if st.session_state.current_agent != agent_data["id"]:
    st.session_state.messages = [{"role": "assistant", "content": agent_data["welcome"]}]
    st.session_state.current_agent = agent_data["id"]

# --- CHAT RENDERING ---
st.title(f"Agent: {choice}")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- MESSAGE PROCESSING ---
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # Context injection logic
        final_input = prompt
        
        if agent_data["id"] == "hal":
            info = search_property_info(prompt)
            if info: final_input += f"\n\n[SEARCH DATA]:\n{info}"
        
        if agent_data["id"] == "simon":
            date_str = datetime.now().strftime("%B %d, %Y")
            final_input = f"DATE: {date_str}\nINPUT: {prompt}"

        # Gemini Call
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=agent_data["system"]
        )

        # History mapping for API
        history = []
        for m in st.session_state.messages[:-1]:
            role = "user" if m["role"] == "user" else "model"
            history.append({"role": role, "parts": [m["content"]]})

        try:
            chat = model.start_chat(history=history)
            response = chat.send_message(final_input)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
        except Exception as e:
            st.error(f"Error generating response: {e}")
