import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "phi3:mini"

def ask_phi3(prompt: str):

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are a senior static code analyst. Only return useful answers."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }

    try:
        res = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        res.raise_for_status()
        data = res.json()

        if "message" not in data:
            return None

        return data["message"]["content"].strip()

    except requests.exceptions.Timeout:
        return None

    except requests.exceptions.RequestException:
        return None

    except Exception:
        return None