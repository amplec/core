from typing import Optional
from utils.logger import Logger
import requests, uuid, os
from dotenv import load_dotenv

class Amplec:
    """
    This class is named after the amplec project, as this class will house the most important core functionalities for this project.
    """
    
    def __init__(self, logger:Logger, global_system_prompt:Optional[str]=None):
        """
        This is the constructor method for the Amplec class
        
        :param logger: This is a Logger object from the Amplec Utils pip Module.
        :type logger: Logger
        :param global_system_prompt: IF you set this, it will override the default system prompt, which ONLY will be used if the user does not provide a system prompt himself.
        :type global_system_prompt: Optional[str]
        """
        self.log = logger
        
        load_dotenv()
        self.karton_result_api_url = os.getenv("KARTON_RESULT_API_URL")
        if not self.karton_result_api_url:
            raise ValueError("KARTON_RESULT_API_URL is not set")
        
        if global_system_prompt:
            self.system_prompt = global_system_prompt
        else:
            self.system_prompt = "You are a helper system for a malware analyst. You will be provided with data from a malware analysis system. Your task is it to answer the questions from the analyst. Do not guess or infer. If some information is not available, just say so."
            
    
    def process(self, karton_submission_id:str, regex:Optional[str]=None):
        """
        This method will process the submitted data and return the result
        """
        
        
        karton_result = self._retrieve_karton_result(karton_submission_id)
        self.log.info(f"Succesfully retrieved karton result with ID {karton_submission_id}")
        
        return "Processing Worked!"
        
        
    def _retrieve_karton_result(self, submission_id:str) -> dict:
        """
        This method will retrieve the karton result from the karton api
        
        :param submission_id: This is the submission id for the karton result.
        :type submission_id: str
        :return: The karton result
        :rtype: dict
        """
        
        response = requests.get(url=f"{self.karton_result_api_url}submissions/{submission_id}", timeout=30)
        
        if response.status_code == 200:
            return response.json()
            
        elif response.status_code == 404:
            if not self._check_for_validity_of_uuid(submission_id):
                raise ValueError(f"Karton does not find the submission with ID {submission_id}, ALSO the provided ID is not a valid UUID!")
            raise ValueError(f"Submission with ID {submission_id} not found!, probably the submission is not finished yet.")
        
        else:
            raise ValueError(f"Failed to retrieve submission with ID {submission_id}, response: {response.text}")
        
        
    def _check_for_validity_of_uuid(self, uuid_to_check:str) -> bool:
        """
        This method will check if the provided string is a valid UUID
        
        :param uuid_to_check: This is the string to check if it is a valid UUID
        :type uuid_to_check: str
        :return: True if the provided string is a valid UUID, False otherwise
        :rtype: bool
        """
        
        try:
            uuid_obj = uuid.UUID(uuid_to_check, version=4)
            return str(uuid_obj) == uuid_to_check
        except ValueError:
            self.log.warning(f"Provided string {uuid_to_check} is not a valid UUID!")
            return False