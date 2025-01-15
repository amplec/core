from typing import Optional
from utils.logger import Logger
from utils.simple_persistence import SimplePersistence
import requests, uuid, os
from dotenv import load_dotenv
from preprocessing.karton_preprocessor import KartonPreprocessor

class Amplec:
    """
    This class is named after the amplec project, as this class will house the most important core functionalities for this project.
    """
    
    def __init__(self, logger:Logger, persistence_folder_path:str):
        """
        This is the constructor method for the Amplec class
        
        :param logger: This is a Logger object from the Amplec Utils pip Module.
        :type logger: Logger
        :param persistence_folder_path: This is the folder path where the persistence data will be stored.
        :type persistence_folder_path: str
        """
        self.log = logger
        
        load_dotenv()
        self.karton_result_api_url = os.getenv("KARTON_RESULT_API_URL")
        if not self.karton_result_api_url:
            raise ValueError("KARTON_RESULT_API_URL is not set")
        
        self.persistence = SimplePersistence(persistence_folder_path, logger)
        
        self.log.info("Amplec initialized")
    
    def _process_submission_ID(self, karton_submission_id:str, regex:str, repreprocess:Optional[bool]=False) -> list[str]:
        """
        This method will process the submitted data and return the result
        
        :param karton_submission_id: This is the submission ID for the karton result
        :type karton_submission_id: str
        :param regex: This is an optional regex to filter the data
        :type regex: str
        :param repreprocess: This is an optional parameter to reprocess the data, defaults to False
        :type repreprocess: Optional[bool]
        """
        
        if not repreprocess:
            try:
                preprocessed_data = self.persistence.load_only_payload(karton_submission_id)
                self.log.info(f"Successfully loaded preprocessed data with ID {karton_submission_id}")
            except FileNotFoundError:
                self.log.info(f"Preprocessed data with ID {karton_submission_id} not found, will retrieve it from karton, and process it ourselves.")
                repreprocess = True
        if repreprocess:        
            karton_result = self._retrieve_karton_result(karton_submission_id)
            self.log.info(f"Succesfully retrieved karton result with ID {karton_submission_id}")
            
            pre = KartonPreprocessor(self.log)
            
            preprocessed_data = pre.process(karton_result)
        
        return preprocessed_data
        
        
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