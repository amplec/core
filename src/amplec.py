from typing import Optional
from utils.logger import Logger
from utils.simple_persistence import SimplePersistence
import requests, uuid, os, re
from dotenv import load_dotenv
from preprocessing.karton_preprocessor import KartonPreprocessor
from preprocessing.nl_preprocessor import NLPreprocessor
from preprocessing.enricher import Enricher

class Amplec:
    """
    This class is named after the amplec project, as this class will house the most important core functionalities for this project.
    Which is Preprocessing, Enriching, Naturalizing and Filtering the data. Also the data will be cached to avoid unnecessary reprocessing.
    """
    
    def __init__(self, logger:Logger, persistence_folder_path:Optional[str]=None) -> None:
        """
        This is the constructor method for the Amplec class
        
        :param logger: This is a Logger object from the Amplec Utils pip Module.
        :type logger: Logger
        :param persistence_folder_path: This is the folder path where the persistence data will be stored. ATTENTION, this is optional, and when not provided the path will be tried to load from the .env file, if neither .env nor parameter is provided, an error will be raised.
        :type persistence_folder_path: Optional[str]
        """
        self.log = logger
        
        load_dotenv()
        self.karton_result_api_url = os.getenv("KARTON_RESULT_API_URL")
        if not self.karton_result_api_url:
            raise ValueError("KARTON_RESULT_API_URL is not set")
        
        if not persistence_folder_path:
            persistence_folder_path = os.getenv("PERSISTENCE_FOLDER_PATH")
            if not persistence_folder_path:
                raise ValueError("PERSISTENCE_FOLDER_PATH is not set, and the variable was also not provided to the constructor")
        
        self.persistence = SimplePersistence(persistence_folder_path, logger)
        
        self.log.info("Amplec initialized")
        
    def generate_llm_data_input_from_submission_id(self, karton_submission_id:str, regex_or_search:str, use_regex:bool, reprocess:Optional[bool]=False) -> list[str]:
        """
        This method will generate the INPUT DATA for the LLM. This method will return a list of strings which underwent the following steps.
        
        1. Karton Submission ID is used to retrieve the karton result from the result API
        2. The karton result is preprocessed by the KartonPreprocessor, this includes:
            a) Normalizing and Cleaning the data
            b) Retrieving further data, such as Triage Results.
        3. The preprocessed data (at this stage still as JSON) is *naturalized* (turned into a list of sentences in human readable form)
        4. The naturalized data is then enriched currently this includes:
            a) Adding Context Blocks to ttps found in the data
            b) more to come...
        5. The enriched data is then filtered. This can be done by providing a regex or search string. Depending on the use_regex bool, the regex_or_search String will be used as a regex or as a search string.
        
        Generally the enriched data will be stored in a persistence folder and WON'T be reprocessed if the same submission ID is provided again, HOWEVER this can be forced by reprocess bool to True.
        
        :param karton_submission_id: This is the submission ID for the karton result
        :type karton_submission_id: str
        :param regex_or_search: This is a regex or search string to filter the data
        :type regex_or_search: str
        :param use_regex: This is a boolean to determine if the regex_or_search should be used as a regex or search string
        :type use_regex: bool
        :param reprocess: This is an optional parameter to reprocess the data, defaults to False
        :type reprocess: Optional[bool]
        :return: The generated LLM input data
        """
        
        # first we need to get the enriched data (either from persistence or by processing the karton result)
        enriched_data = self._process_submission_ID(karton_submission_id, reprocess)
        
        search_result = []
        if use_regex:
            # Use regex to filter the data
            try:
                pattern = re.compile(regex_or_search)
                search_result = [line for line in enriched_data if pattern.search(line)]
            except re.error as e:
                raise ValueError(f"Invalid regex pattern: {regex_or_search}") from e
        else:
            # Use plain search string to filter the data (case-insensitive)
            for line in enriched_data:
                lower_line = line.lower()
                lower_search = regex_or_search.lower()
                if lower_search in lower_line:
                    search_result.append(line)
        
        if not search_result:
            self.log.warning(f"No results found for search '{regex_or_search}' in submission with ID {karton_submission_id}")
        
        return search_result
        
    
    def _process_submission_ID(self, karton_submission_id:str, repreprocess:Optional[bool]=False) -> list[str]:
        """
        This method will process the submitted data and return the result
        
        :param karton_submission_id: This is the submission ID for the karton result
        :type karton_submission_id: str
        :param repreprocess: This is an optional parameter to reprocess the data, defaults to False
        :type repreprocess: Optional[bool]
        :return: The data
        """
        
        if not repreprocess:
            try:
                enriched_data = self.persistence.load_only_payload(karton_submission_id)
                self.log.info(f"Successfully loaded preprocessed data with ID {karton_submission_id}")
            except FileNotFoundError:
                self.log.info(f"Preprocessed data with ID {karton_submission_id} not found, will retrieve it from karton, and process it ourselves.")
                repreprocess = True
        if repreprocess:        
            karton_result = self._retrieve_karton_result(karton_submission_id)
            self.log.info(f"Succesfully retrieved karton result with ID {karton_submission_id}")
            
            pre = KartonPreprocessor(self.log)
            preprocessed_data = pre.process(karton_result)
            
            nlp = NLPreprocessor(self.log)        
            naturalized_data = nlp.naturalize(preprocessed_data)
            
            enr = Enricher(self.log, "preprocessing/mitre_techniques.json")
            enriched_data = enr.process(naturalized_data)
            
            self.persistence.store_submission(karton_submission_id, enriched_data)
        
        return enriched_data
        
        
    def _retrieve_karton_result(self, submission_id:str) -> dict:
        """
        This method will retrieve the karton result from the karton api
        
        :param submission_id: This is the submission id for the karton result.
        :type submission_id: str
        :return: The karton result
        :rtype: dict
        """
        
        response = requests.get(url=f"{self.karton_result_api_url}submissions/{submission_id}", timeout=120)
        
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