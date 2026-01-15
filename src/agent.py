import requests
import json
import subprocess
import os
import sys

# CONFIGURATION (Loaded from Environment for Security)
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("❌ ERROR: GEMINI_API_KEY environment variable not set.")
    print("👉 Run: export GEMINI_API_KEY='your_key_here'")
    sys.exit(1)

# Use the reliable model
MODEL = "gemini-2.0-flash-exp"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

def get_k8s_logs(pod_name):
    try:
        # Fetch last 50 lines
        cmd = f"kubectl logs -l app={pod_name} --tail=50"
        result = subprocess.check_output(cmd, shell=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        return f"Error fetching logs: {e}"

def ask_gemini(logs):
    print("🚀 Sending logs to AI Agent...")
    prompt = f"""
    You are a Senior Site Reliability Engineer. 
    Analyze these Kubernetes logs for errors.
    
    Logs:
    {logs}
    
    Task:
    1. Identify the HTTP status code and error message.
    2. Suggest a specific kubectl command to verify the pod status.
    3. Suggest a fix for the underlying issue.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    elif response.status_code == 429:
        return "⚠️ API Limit Reached (429). Please wait 60 seconds."
    else:
        return f"API Error {response.status_code}: {response.text}"

def main():
    print("--- 🤖 AI SRE AGENT INITIALIZED ---")
    print("Monitoring cluster for 'broken-app'...")
    
    # 1. Fetch real logs
    logs = get_k8s_logs("broken-app")
    
    if "Error" not in logs and "500" not in logs:
        print("✅ No errors detected in recent logs.")
        # We proceed anyway for the demo
    
    print(f"\n📄 Captured Logs:\n{logs[:200]}...\n") 
    
    # 2. Consult the AI
    analysis = ask_gemini(logs)
    
    print("\n--- 🧠 AI DIAGNOSIS ---")
    print(analysis)
    print("-----------------------")

if __name__ == "__main__":
    main()
