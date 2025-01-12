from utils.logger import Logger



class Preprocessor:
    """
    This class is implemented as a parent class for all preprocessor classes.
    
    """
    
    def __init__(self, logger:Logger) -> None:
        """
        Constructor for the Preprocessor-class
        
        :param logger: This is a Logger object from the Amplec Utils pip Module.
        :type logger: Logger
        """
        self.log = logger
        
    def process(self, data:dict) -> dict:
        """
        Processes the input data
        **NOT IMPLEMENTED**
        
        :param data: input data to be processed
        :type data: dict
        :return: processed data
        """
        
        raise NotImplementedError("The process method has not been implemented")