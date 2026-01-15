import requests
import json
import subprocess
import os
import sys
import time

# CONFIGURATION
# Options: "google" or "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "google") 

# Google Config
# SECURE: Read from Environment Variable (Do NOT paste key here)
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_MODEL = "gemini-2.0-flash-exp"

# Ollama Config (Internal K8s DNS)
OLLAMA_URL = "http://ollama-svc.default.svc.cluster.local:80/api/generate"
OLLAMA_MODEL = "gemma:2b" 

def get_k8s_logs(pod_name):
    try:
        cmd = f"kubectl logs -l app={pod_name} --tail=50"
        result = subprocess.check_output(cmd, shell=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        return f"Error fetching logs: {e}"

def ask_google(prompt):
    if not GOOGLE_API_KEY:
        return "❌ Error: GEMINI_API_KEY is missing. Did you run 'export GEMINI_API_KEY=...'?"
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GOOGLE_MODEL}:generateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        return f"Google API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Connection Error: {e}"

def ask_ollama(prompt):
    print(f"🦙 Consulting Local LLM ({OLLAMA_MODEL})...")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()['response']
        return f"Ollama Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Ollama Connection Error: {e}"

def main():
    print("--- 🤖 AI SRE AGENT V2 (Hybrid) ---")
    print(f"🔌 Active Provider: {LLM_PROVIDER.upper()}")
    
    logs = get_k8s_logs("broken-app")
    print(f"\n📄 Captured Logs:\n{logs[:200]}...\n") 
    
    prompt = f"""
    Analyze these Kubernetes logs for errors.
    Logs:
    {logs}
    
    1. Identify the HTTP status code.
    2. Suggest a specific kubectl fix.
    """
    
    if LLM_PROVIDER == "ollama":
        analysis = ask_ollama(prompt)
    else:
        analysis = ask_google(prompt)
    
    print("\n--- 🧠 AI DIAGNOSIS ---")
    print(analysis)
    print("-----------------------")

if __name__ == "__main__":
    main()
