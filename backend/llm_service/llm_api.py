# llm_service.py
from openai import OpenAI
from config.settings import DEEPSEEK_API_KEY


class LLM_Service:
    def __init__(self):
        # Initialize OpenAI client for DeepSeek on OpenRouter
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=DEEPSEEK_API_KEY,
        )
        self.model = "google/gemma-3-27b-it:free"

    def get_completion(self, message: str) -> str:
        """
        Send a processed prompt to the LLM and return its response.
        
        Args:
            message (str): The user's query or processed prompt.
        
        Returns:
            str: The model's textual response.
        """
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": message}
                ]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error while contacting LLM: {e}"

