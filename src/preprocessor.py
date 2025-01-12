from utils.logger import Logger
import requests, os
from dotenv import load_dotenv
from typing import List


class Preprocessor:
    """
    This class will be used to preprocess the input data for the LLM.
    """
    
    def __init__(self, logger:Logger) -> None:
        """
        Constructor for the Preprocessor-class
        """
        load_dotenv()
        self.api_key = os.getenv("TRIAGE_API_KEY")
        if self.api_key is None:
            raise ValueError("TRIAGE_API_KEY is not set")
        self.triage_url = os.getenv("TRIAGE_URL")
        self.log = logger
        
        
    def process(self, data:dict) -> dict:
        """
        Processes the input data (we assume that the data is in a Karton Result Api format)
        
        :param data: input data to be processed
        :type data: dict
        :return: processed data
        """
        
        ret_data = {
            "payload_results": self._process_payload_results(data.get("payload_results", {}))
        }
        
        return ret_data      
                
    def _process_payload_results(self, payload_results:dict) -> dict:
        """
        This method is specifically used to process the payload results.
        
        It will:
            - Remove empty result entries
            - further process result entries
        
        :param payload_results: payload results to be processed
        :type payload_results: dict
        :return: processed payload results    
        """        
        
        processed_payload_results = {}
        
        for key in payload_results.keys():
            if payload_results[key]:
                processed_payload_results[key] = self._process_result_list(payload_results[key])
        
        return processed_payload_results

    def _process_result_list(self, result_entries:list) -> list:
        """
        This method will process a list of result entries
        
        :param result_entries: list of result entries to be processed
        :type result_entries: list
        :return: processed result entries
        """
        
        processed_result_entries = []
        
        for entry in result_entries:
            processed_result_entries.append(self._process_result_entry(entry))
        
        return processed_result_entries
    
    def _process_result_entry(self, result_entry:dict) -> dict:
        """
        This method will process a single result entry
        
        :param result_entry: result entry to be processed
        :type result_entry: dict
        :return: processed result entry
        """
        return_entry = {}
        source = result_entry.get("created_by", "").replace("karton-", "")
        return_entry["payload_type"] = result_entry.get("payload_type", "")
        return_entry["type"] = source
        return_entry["data"] = {}
        return_entry["payload_id"] = result_entry.get("payload_id", "")
        return_entry["timestamp"] = result_entry.get("created_at", "")
        
        match source:
            case "triage":
                # Extract submission id
                submission_id = result_entry.get("data", {}).get("submission_id", "")
                if submission_id:
                    triage_overview = self._retrieve_triage_overview(submission_id)
                    return_entry["data"] = triage_overview
                else:
                    self.log.error(f"Failed to extract Submission ID from a detected triage result entry! payload_id: {result_entry.get('payload_id', 'N/A')}")
                
            case _:
                return_entry["data"] = result_entry.get("data", {})
                
        return return_entry
            
                
                
    def _retrieve_triage_overview(self, triage_id:str) -> dict:
        """
        Retrieves the triage overview for a given triage id
        
        :param triage_id: triage id for which the overview should be retrieved
        :type triage_id: str
        :return: triage overview
        """
        
        return_dict = {}
        
        self.log.info(f"Retrieving triage overview for triage id: {triage_id}")
        
        #response = requests.get(url=f"{self.triage_url}samples/{triage_id}/behavioral1/report_triage.json", headers={"Authorization": f"Bearer {self.api_key}"})
        
        response = requests.get(url=f"{self.triage_url}samples/{triage_id}/overview.json", headers={"Authorization": f"Bearer {self.api_key}"})
        
        if response.status_code != 200:
            self.log.error(f"Failed to retrieve triage overview for triage id: {triage_id}")
            self.log.error(f"Response: {response.text}")
        else:
            return_dict["analysis"] = response.json().get("analysis", {})
            
            sample = response.json().get("sample", {})
            return_dict["sha256"] = sample.get("sha256", "")
            return_dict["timestamp"] = sample.get("completed", "")
            return_dict["id"] = sample.get("id", "")
            
            return_dict["signatures"] = response.json().get("signatures", [])
            
            targets = response.json().get("targets", [])
            return_dict["iocs"] = {
                "ips": [],
                "urls": [],
                "domains": [],
                "emails": [],
            }
            for target in targets:
                iocs = target.get("iocs", {})
                for domain in iocs.get("domains", []):
                    if domain not in return_dict["iocs"]["domains"] and not "in-addr.arpa" in domain:
                        return_dict["iocs"]["domains"].append(domain) 
                for ip in iocs.get("ips", []):
                    if ip not in return_dict["iocs"]["ips"]:
                        return_dict["iocs"]["ips"].append(ip)
                for url in iocs.get("urls", []):
                    if url not in return_dict["iocs"]["urls"]:
                        return_dict["iocs"]["urls"].append(url)
                for email in iocs.get("emails", []):
                    if email not in return_dict["iocs"]["emails"]:
                        return_dict["iocs"]["emails"].append(email)

        return return_dict
    