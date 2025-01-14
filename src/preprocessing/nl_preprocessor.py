from utils.logger import Logger
from typing import List, Union, Optional
from collections.abc import Iterable
from .preprocessor import Preprocessor

class NLPreprocessor(Preprocessor):
    """
    This class will serve as a Translator from JSON structurized data into a more natural language equivalent text.
    """
    
    def __init__(self, logger:Logger) -> None:
        """
        Constructor for the NLPreprocessor-class
        """
        
        super().__init__(logger)
        
        self.headline_keywords = {
            "sha256": "#sha256 <replace> ",
            "label": "<replace>",
            "name": "<replace>",
            "description": "<replace>",
        }
        
        self.headline_key_keywords = {
            "signatures": "has the signature <replace> ",
            "indicators": "with the indicator <replace> ",
            "analysis": "has an analysis ",
        }
        self.log.info("NLPreprocessor initialized")
    
    def naturalize(self, data:dict) -> List[str]:
        """
        Translates the JSON structurized data into a more natural language equivalent text.
        
        This method expects a JSON looking like this:
        ```json
        {
            "configs": {...},
            "hierarchy": {...},
            "results": {...},
            "triage_results": {...},
        }
        ```
        
        :param data: JSON structurized data
        :type data: dict
        :return: natural language equivalent text
        """
        
        naturalized_data = []
        try:
            #naturalized_data.extend(self.naturalize_configs(data["configs"]))
            #naturalized_data.extend(self.naturalize_hierarchy(data["hierarchy"]))
            #naturalized_data.extend(self.naturalize_results(data["results"]))
            for key, value in data["triage_results"].items():
                naturalized_data.extend(self.naturalize_triage_results(value))
        except KeyError as e:
            self.log.error(f"Naturalize could not find the data for the key {e}")
               
        return naturalized_data
    
    
    def naturalize_triage_results(self, data:dict) -> List[str]:
        """
        This method will be used to only naturalize the triage results
        :param data: triage results
        :type data: dict
        :return: naturalized triage results
        """
        
        naturalized_data = []
         
        headline = self._search_for_headline(data)
        
        naturalized_data.extend(self._recursive_naturalize(data, headline))
        
        return naturalized_data
    
    def _search_for_headline(self, data:dict) -> str:
        """
        Searches for a headline in the data
        
        :param data: data to be searched
        :type data: dict
        :return: headline
        """
        
        headline = ""
        if isinstance(data, dict):
            for key in self.headline_keywords.keys():
                if key in data.keys():
                    headline = self.headline_keywords[key].replace("<replace>", data[key])
                    break
        if headline == "":
            self.log.warning(f"Could not find a headline in the data, using default headline")
            headline = "with data "
        else:
            self.log.info(f"Found headline: {headline}")
        
        return headline
    
    def _build_headline(self, data:Union[dict, List, str, int, bool, float], key:Optional[str]=None) -> str:
        """
        This method will build a headline based on the key and the data present, if there is a headline keyword in the data this will also be used.
        
        :param data: data to be used to build the headline
        :type data: dict
        :param key: key under which the data was stored
        :type key: Optional[str]
        :return: headline
        """
        
        headline = ""
        
        if key is None:
            if isinstance(data, dict):
                headline = "with "
            elif isinstance(data, list):
                headline = "containing "
            else:
                headline = "with value "
        
        elif key in self.headline_key_keywords.keys():
            headline = self.headline_key_keywords[key].replace("<replace>", self._search_for_headline(data))
        
        else:
            headline = f"with {key} "
            
        return headline
            
    
    def _recursive_naturalize(self, data:Union[dict, list], prefix:str) -> List[str]:
        """
        Recursively naturalizes the data
        
        :param data: data to be naturalized (can be a dict or a list)
        :type data: Union[dict, list]
        :param prefix: prefix to be added to the naturalized data
        :type prefix: str
        :return: naturalized data
        """
        
        naturalized_data = []
        
        # first we check if the data present is a leaf, because this is the breaking condition for the recursion
        if self._check_for_leaf(data):
            naturalized_data.append(f"{prefix}{self._handle_leaf(data)}")
        
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, list) and not self._check_for_leaf(value) and isinstance(value[0], dict):
                    # this is our special little case where we need to handle this differently
                    self.log.info(f"Found a special case, handling it differently")
                    for entry in value:
                        headline = self._build_headline(entry, key)
                        if "with data" in headline:
                            headline = "with "
                        naturalized_data.extend(self._recursive_naturalize(entry, f"{prefix}{headline}"))
                else:
                    headline = self._build_headline(value, key)
                    naturalized_data.extend(self._recursive_naturalize(value, f"{prefix}{headline}"))
        
        elif isinstance(data, list):
            for entry in data:
                naturalized_data.extend(self._recursive_naturalize(entry, prefix))
        
        else:
            self.log.error(f"Data is neither a dict nor a list and not a leaf, this should not happen! Type of data: {type(data)}")
        
        return naturalized_data
        
    def _handle_leaf(self, leaf:any) -> str:
        """
        Handles a leaf in the data
        
        :param leaf: leaf to be handled
        :type leaf: any
        :return: naturalized leaf
        """
        
        ret_str = ""
        
        if isinstance(leaf, dict):
            for key, value in leaf.items():
                ret_str += f"{key}: {value}, "
        elif isinstance(leaf, list):
            for entry in leaf:
                ret_str += f"{entry}, "
        else:
            ret_str = f"{leaf}"
        
        return ret_str
    
    
    def _check_for_leaf(self, leaf_candidate:any) -> bool:
        """
        Checks if the leaf candidate is a leaf
        
        :param leaf_candidate: candidate to be checked
        :type leaf_candidate: any
        :return: True if the leaf_candidate is a leaf, False otherwise
        """
        
        is_leaf = True
        
        if isinstance(leaf_candidate, dict):
            for key, value in leaf_candidate.items():
                if isinstance(value, Iterable) and not isinstance(value, str):
                    is_leaf = False
                    break
        
        elif isinstance(leaf_candidate, Iterable) and not isinstance(leaf_candidate, str):
            for entry in leaf_candidate:
                if isinstance(entry, Iterable) and not isinstance(entry, str):
                    is_leaf = False
                    break
        
        return is_leaf