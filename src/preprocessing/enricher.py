from utils.logger import Logger
from .preprocessor import Preprocessor
from typing import List, Union, Optional, override
import re, json


class Enricher(Preprocessor):
    """
    This class serves as an enrichment step for the preprocessed and naturalized data.
    """
    
    def __init__(self, logger:Logger, ttp_context_path:str) -> None:
        """
        Constructor for the Enricher-class
        """
        
        self.ttp_context = {}
        
        with open(ttp_context_path, "r") as f:
            self.ttp_context = json.load(f)
        
        super().__init__(logger)
        
        self.log.info("Enricher initialized")
     
    @override   
    def process(self, data:List[str]) -> List[str]:
        """
        This Method will enrich the normalized data with additional information.
        :param data: normalized data
        :type data: List[str]
        :return: enriched data
        """
        
        enriched_data_to_be_added = []
        
        # Enrich for Used TTPs
        ttp_containing_sentences = [sentence for sentence in data if re.search(r"T\d{4}(\.\d{3})?", sentence)]
        enriched_data_to_be_added.extend(self._enrich_ttps(ttp_containing_sentences))
        
        
        
        return data.extend(enriched_data_to_be_added)
    
    def _enrich_ttps(self, ttp_containing_sentences:List[str]) -> str:
        """
        This method will provide addt
        
        :param ttp_containing_sentences: The sentences, which contain ttps and need context
        :type ttp_containing_sentences: List[str]
        :return: sentence(s) with context information about the ttps
        """
        
        context_sentences = []
        
        ttps = set()
        for sentence in ttp_containing_sentences:
            ttp_list = re.findall(r"T\d{4}(\.\d{3})?", sentence)
            for ttp in ttp_list:
                ttps.add(ttp)
        
        for ttp in ttps:
            if not ttp in self.ttp_context.keys():
                self.log.error(f"No context information found for TTP: {ttp}")
                continue
            context = self.ttp_context[ttp]
            context_sentences.append(f"TTP {ttp} has the name {context['name']} and the description {context['description']}")
        
        return context_sentences
    
    