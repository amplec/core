from utils.logger import Logger
from dotenv import load_dotenv
import os
from ollama import Client
from typing import Optional


class Chatter:
    """
    This class's main purpose is to provide "chatting" functionalities to the Amplec project.
    This means mainly interacting with the LLM and handling the conversations.
    """
    
    def __init__(self, logger:Logger, model:str):
        """
        This is the constructor method for the Chatter class
        
        :param logger: This is a Logger object from the Amplec Utils pip Module.
        :type logger: Logger
        :param model: This is a string with the model to use in the chat
        :type model: str
        """
        self.log = logger
        
        self.model = model
        load_dotenv()
        
        self.api_key = os.getenv("OLLAMA_API_KEY")
        self.url = os.getenv("OLLAMA_URL")
        
        if not self.api_key:
            raise ValueError("OLLAMA_API_KEY is not set")
        if not self.url:
            raise ValueError("OLLAMA_URL is not set")
        
        custom_kwargs_for_hxxp_client = {
            "headers": {
                "Authorization": f"Bearer {self.api_key}",
            },
            "verify": False,
        }
        
        self.client = Client(self.url, **custom_kwargs_for_hxxp_client)
        
    def chat(self, messages:list[str], override_model:Optional[str]=None) -> str:
        """
        This method will chat with the llm and return the result
        
        :param messages: This is a list of strings with the messages to chat with the llm
        :type messages: list[str]
        :param override_model: This is a string with the model to use in the chat, IF you want to override the model set by the object.
        :type override_model: Optional[str]
        """
        
        model = override_model if override_model else self.model
        
        response = self.client.chat(messages=messages, model=model)
        
        if not response.get("message"):
            self.log.error("No messages in response!, response: " + str(response))
            raise ValueError("No messages in response " + str(response))
        
        if not response.get("message").get("content"):
            self.log.error("No content in messages!, response: " + str(response))
            raise ValueError("No content in messages")
        
        return response.get("message").get("content")
        
        
        