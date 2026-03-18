import os
import sys
import time
import subprocess
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import requests

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_MODEL = "gemini-2.0-flash-exp"

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "ollama-svc")
OLLAMA_PORT = os.getenv("OLLAMA_PORT", "80")
OLLAMA_NAMESPACE = os.getenv("OLLAMA_NAMESPACE", "default")
OLLAMA_URL = f"http://{OLLAMA_HOST}.{OLLAMA_NAMESPACE}.svc.cluster.local:{OLLAMA_PORT}/api/generate"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
OLLAMA_MAX_RETRIES = int(os.getenv("OLLAMA_MAX_RETRIES", "3"))


def get_k8s_logs(pod_label):
    try:
        result = subprocess.run(
            ["kubectl", "logs", "-l", f"app={pod_label}", "--tail=50"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if result.returncode != 0:
            return f"Error fetching logs: {result.stderr}"
        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error: kubectl command timed out"
    except FileNotFoundError:
        return "Error: kubectl not found in PATH"
    except Exception as e:
        return f"Error fetching logs: {e}"


def create_session_with_retries(retries=3, backoff_factor=1.0):
    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST", "GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def ask_google(prompt):
    if not GOOGLE_API_KEY:
        return (
            "Error: GEMINI_API_KEY is missing. Did you run 'export GEMINI_API_KEY=...'?"
        )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GOOGLE_MODEL}:generateContent?key={GOOGLE_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        session = create_session_with_retries()
        response = session.post(url, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return f"Google API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Connection Error: {e}"


def ask_ollama(prompt):
    print(f"🦙 Consulting Local LLM ({OLLAMA_MODEL})...")
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}

    for attempt in range(OLLAMA_MAX_RETRIES):
        try:
            session = create_session_with_retries(retries=1, backoff_factor=0.5)
            response = session.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
            if response.status_code == 200:
                return response.json()["response"]
            if response.status_code == 404:
                return f"Ollama Error: Model '{OLLAMA_MODEL}' not found. Pull it with: kubectl exec -it deployment/ollama -- ollama pull {OLLAMA_MODEL}"
            return f"Ollama Error: {response.status_code} - {response.text}"
        except requests.exceptions.Timeout:
            if attempt < OLLAMA_MAX_RETRIES - 1:
                wait_time = (attempt + 1) * 2
                print(
                    f"Timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{OLLAMA_MAX_RETRIES})"
                )
                time.sleep(wait_time)
                continue
            return "Ollama Error: Connection timeout after retries"
        except requests.exceptions.ConnectionError as e:
            if attempt < OLLAMA_MAX_RETRIES - 1:
                wait_time = (attempt + 1) * 2
                print(
                    f"Connection error, retrying in {wait_time}s... (attempt {attempt + 1}/{OLLAMA_MAX_RETRIES})"
                )
                time.sleep(wait_time)
                continue
            return f"Ollama Connection Error: {e}"
        except Exception as e:
            return f"Ollama Error: {e}"

    return "Ollama Error: Max retries exceeded"


def main():
    print("--- 🤖 AI SRE AGENT V3 (Secure) ---")
    print(f"🔌 Active Provider: {LLM_PROVIDER.upper()}")
    print(f"📡 Ollama URL: {OLLAMA_URL}")

    pod_name = os.getenv("POD_NAME", "broken-app")
    logs = get_k8s_logs(pod_name)

    if logs.startswith("Error"):
        print(f"❌ {logs}")
        sys.exit(1)

    print(f"\n📄 Captured Logs:\n{logs[:200]}...\n")

    prompt = f"""Analyze these Kubernetes logs for errors.
Logs:
{logs}

1. Identify the HTTP status code.
2. Suggest a specific kubectl fix."""

    if LLM_PROVIDER == "ollama":
        analysis = ask_ollama(prompt)
    else:
        analysis = ask_google(prompt)

    print("\n--- 🧠 AI DIAGNOSIS ---")
    print(analysis)
    print("-----------------------")


if __name__ == "__main__":
    main()
