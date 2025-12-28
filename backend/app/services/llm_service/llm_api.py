# llm_service.py
import requests
import json


class LLM_Service:
    def __init__(self):
        self.base_url = "http://localhost:11434/api"
        self.model = "vigogne-7b"

    def get_completion(self, message: str) -> str:
        """
        Send a prompt to the local Ollama LLM and return its response.
        """
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": message}
                    ],
                    "stream": False
                },
                timeout=300
            )

            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

        except Exception as e:
            return f"Error while contacting local LLM: {e}"

    def get_completion_stream(self, message: str):
        """
        Streaming completion - yields chunks of text as they arrive.
        """
        try:
            with requests.post(
                f"{self.base_url}/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": message}
                    ],
                    "stream": True
                },
                stream=True,
                timeout=300
            ) as response:

                response.raise_for_status()

                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]

        except Exception as e:
            yield f"Error while contacting local LLM: {e}"
