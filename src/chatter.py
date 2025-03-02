from utils.logger import Logger
from dotenv import load_dotenv
import os
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Optional
from amplec import Amplec


class Chatter:
    """
    This class's main purpose is to provide "chatting" functionalities to the Amplec project.
    This means mainly interacting with the LLM and handling the conversations.
    """
    
    def __init__(self, logger:Logger, model:str, amplec_persistence_folder_path:Optional[str]=None, override_submission_id:Optional[str]=None, openai_api_key:Optional[str]=None) -> None:
        """
        This is the constructor method for the Chatter class
        
        :param logger: This is a Logger object from the Amplec Utils pip Module.
        :type logger: Logger
        :param model: This is a string with the model to use in the chat
        :type model: str
        :param amplec_persistence_folder_path: This is the folder path where the persistence data will be stored. ATTENTION, this is optional, and when not provided the path will be tried to load from the .env file, if neither .env nor parameter is provided, an error will be raised.
        :type amplec_persistence_folder_path: Optional[str]
        :param override_submission_id: This is a string with the submission ID to override the submission ID for the use in the tool_call.
        :type override_submission_id: Optional[str]
        :param openai_api_key: This is a string with the OpenAI API Key to use in the chat
        :type openai_api_key: Optional[str]
        """
        self.log = logger
        
        self.model = model
        load_dotenv()
        
        self.url = os.getenv("OLLAMA_URL")
        self.amplec = Amplec(logger, amplec_persistence_folder_path)
        if override_submission_id:
            self.override_submission_id = override_submission_id
        
        if not self.url:
            raise ValueError("OLLAMA_URL is not set")
        self.openai_api_key = openai_api_key
        
        self.reprocess = False
           
    def chat(self, system_message:str, user_message:str, use_tool_calling:Optional[bool]=False, override_model:Optional[str]=None, reprocess:Optional[bool]=False) -> str:
        """
        This method will chat with the llm and return the result
        
        :param system_message: This is the system message to start the conversation
        :type system_message: str
        :param user_message: This is the user message to start the conversation
        :type user_message: str
        :param use_tool_calling: This is a bool to indicate if the tool calling should be used default is False
        :type use_tool_calling: Optional[bool]
        :param override_model: This is a string with the model to use in the chat, IF you want to override the model set by the object.
        :type override_model: Optional[str]
        :param reprocess: This is a bool to indicate if the data should be reprocessed, default is False
        :type reprocess: Optional[bool]
        """
        
        model = override_model if override_model else self.model
        self.reprocess = reprocess
        if model in ["gpt-4o", "gpt-4o-mini"]:
            if not self.openai_api_key:
                raise ValueError("You need to provide an API key for the GPT-4 API")
            chat = ChatOpenAI(model=model, api_key=self.openai_api_key)
            if self.override_submission_id:
                user_message = user_message + " " + self.override_submission_id
        else:
            chat = ChatOllama(base_url=self.url, model=model, temperature=0.1)
        
        @tool
        def search_for_sample_info(sample_id: str, search_term:str) -> str:
            """Get the search results for a given search term in the context of a malware sample.
            For example, a search term could be "ttp" for the Tactics, Techniques, and Procedures used by the malware, or "url" for URLs found in the malware.
            Only use one search term at a time, for example "domain" or "ttp" BUT NEVER two terms in one operation like "domain ttp".

            Args:
                sample_id: The internal identifier of the malware sample
                search_term: The term to search for in the context of the malware sample

            Returns:
                A human readable list of information in regard to the sample. As a multiline string.
            """
            if self.override_submission_id:
                sample_id = self.override_submission_id
                self.log.info("Overriding sample_id with: " + sample_id)
            self.log.info("Searching for sample info with sample_id: " + sample_id + " and search_term: " + search_term)
            try:
                ret_list = self.amplec.generate_llm_data_input_from_submission_id(sample_id, search_term, False, self.reprocess)
                if not ret_list and " " in search_term:
                    self.log.warning("Multiple search terms detected, splitting them and searching for each term separately")
                    for term in search_term.split(" "): 
                        ret_list.extend(self.amplec.generate_llm_data_input_from_submission_id(sample_id, term, False, self.reprocess))
                if not ret_list:
                    ret_list = ["For the given search term, there was no information available, please say so to the user and dont hallucinate!"]
                
                ret_str = ""
                for item in ret_list:
                    ret_str += item + "\n"
            except Exception as e:
                ret_str = "An error occurred: " + str(e)
            
            return ret_str
            
        prompt = [
            SystemMessage(system_message),
            HumanMessage(user_message)
        ]
            
        if use_tool_calling:
            chat = chat.bind_tools([search_for_sample_info]) 
            ai_msg = chat.invoke(prompt)
            if not ai_msg.tool_calls:
                self.log.error("No tools were called in the chat! ai_msg: " + str(ai_msg))
            if model in ["gpt-4o", "gpt-4o-mini"]:
                prompt.append(ai_msg)
            for tool_call in ai_msg.tool_calls:
                selected_tool = {"search_for_sample_info": search_for_sample_info}[tool_call["name"].lower()]
                tool_msg = selected_tool.invoke(tool_call)
                prompt.append(tool_msg)
        
        llm_response = chat.invoke(prompt)
        
        if not llm_response.content:
            self.log.error("No content in the llm_response, response: " + str(llm_response))
            raise ValueError("No content response")
        
        return llm_response.content    