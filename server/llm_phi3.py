import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "phi3:mini"

def ask_phi3(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a senior static code analyst."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        res = requests.post(OLLAMA_URL, json=payload, timeout=120)
        res.raise_for_status()
        data = res.json()
        return data["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        return f"Ollama error: {str(e)}"
    except Exception as e:
        return f"Ollama parsing error: {str(e)}"