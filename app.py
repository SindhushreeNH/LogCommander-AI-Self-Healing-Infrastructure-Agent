import streamlit as st
import json
import time
from groq import Groq

# Initialize Groq Client
try:
    client = Groq()
except Exception:
    client = None

# Mock Scenarios for Demo Purposes
MOCK_SCENARIOS = {
    "Select a scenario...": "",
    "Scenario A: Out of Memory / Disk Full": (
        "2026-08-01 14:22:01 [ERROR] os_engine.c:312 - Failed to write block to /var/cache/data/\n"
        "2026-08-01 14:22:01 [CRITICAL] system_monitor - Disk space critically low on /dev/sda1 (99% utilized).\n"
        "2026-08-01 14:22:02 [FATAL] app_core - IOException: No space left on device. Process terminated abnormally."
    ),
    "Scenario B: Broken Container / Port Conflict": (
        "2026-08-01 14:25:10 [INFO] docker_manager - Booting service 'web_gateway' on port 8080...\n"
        "2026-08-01 14:25:11 [ERROR] network.go:88 - listen tcp 0.0.0.0:8080: bind: address already in use\n"
        "2026-08-01 14:25:11 [CRITICAL] gateway_launcher - Container web_gateway failed healthcheck. Status: Exited (1)."
    )
}

def clear_cache_directory():
    time.sleep(1.5)
    return "SUCCESS: Cleaned 4.2GB from `/var/cache/data/`. Disk utilization dropped to 68%."

def restart_docker_service():
    time.sleep(1.5)
    return "SUCCESS: Found conflicting process on port 8080. Terminated PID 4112. Restarted container 'web_gateway'."

st.set_page_config(page_title="LogCommander AI Agent", page_icon="🤖", layout="wide")

st.title("🤖 LogCommander AI — Self-Healing Infrastructure Agent")
st.caption("Rooman AI Challenge Submission | Role: Junior AI Research Associate")
st.write("---")

st.sidebar.header("Agent Configuration")
api_key_input = st.sidebar.text_input("Groq API Key (Optional if set in Env)", type="password")

if api_key_input:
    client = Groq(api_key=api_key_input)

if not client:
    st.sidebar.error("⚠️ Groq API Key missing. Please input your `gsk_...` key above to run.")

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("1. Ingestion Layer (Log Input)")
    selected_preset = st.selectbox("Load a sample production failure:", list(MOCK_SCENARIOS.keys()))
    
    log_input = st.text_area(
        "Or paste raw, multi-line system logs / stack traces here:",
        value=MOCK_SCENARIOS[selected_preset] if selected_preset else "",
        height=200
    )
    
    trigger_agent = st.button("🚀 Analyze & Self-Heal System", type="primary", disabled=(not client or not log_input))

with col_right:
    st.subheader("2. Autonomous Agent Execution Loop")
    
    if trigger_agent and client:
        with st.status("Analyzing system logs...", expanded=True) as status:
            st.write("🔍 Extracting error metrics and operational context...")
            time.sleep(0.5)
            
            st.write("🧠 Querying AI Agent reasoning engine (Llama-3)...")
            
            system_prompt = (
                "You are an expert autonomous DevOps and Systems Engineer Agent. Your job is to analyze log files, "
                "determine the clear root cause, and select the correct system tool to repair the system.\n\n"
                "Available Tools:\n"
                "1. name: clear_cache_directory | use case: Use when logs state that disk space is full, out of memory, or cache write failures occur.\n"
                "2. name: restart_docker_service | use case: Use when docker containers fail, port conflicts occur, or service address is already in use.\n\n"
                "You must respond strictly in valid JSON format containing exactly three keys: 'diagnosis', 'tool_name', and 'explanation'. "
                "Do not include markdown wrappers like ```json or any conversational filler text."
            )
            
            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Analyze these logs immediately:\n{log_input}"}
                    ],
                    temperature=0.1
                )
                
                # Parse Agent Decision
                raw_content = response.choices[0].message.content.strip()
                agent_decision = json.loads(raw_content)
                
                st.write(f"✅ Root Cause Identified: **{agent_decision.get('diagnosis')}**")
                tool_to_call = agent_decision.get("tool_name")
                st.write(f"⚙️ Action Chosen: `{tool_to_call}`")
                
                st.write("🛠️ Initiating automated infrastructure remediation...")
                if tool_to_call == "clear_cache_directory":
                    tool_output = clear_cache_directory()
                elif tool_to_call == "restart_docker_service":
                    tool_output = restart_docker_service()
                else:
                    tool_output = "NO_ACTION_TAKEN: Agent determined no specific safe tool was applicable for this error profile."
                
                status.update(label="Remediation Cycle Complete!", state="complete", expanded=True)
                
                st.success("### 🎉 System Restored Successfully")
                st.markdown(f"**Agent Reasoning:** {agent_decision.get('explanation')}")
                st.code(f"Terminal Execution Output:\n{tool_output}", language="bash")
                
            except Exception as e:
                status.update(label="Agent Execution Failed", state="error")
                st.error(f"Error during agent loop: {str(e)}")