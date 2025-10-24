# llm_service.py
from openai import OpenAI
from app.config.settings import DEEPSEEK_API_KEY


class LLM_Service:
    def __init__(self):
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
    
    def get_completion_stream(self, message: str):
        """
        Streaming completion - yields chunks of text as they arrive.
        
        Args:
            message (str): The user's query or processed prompt.
        
        Yields:
            str: Each token/chunk from the model as it's generated.
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": message}
                ],
                stream=True  # Enable streaming
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error while contacting LLM: {e}"