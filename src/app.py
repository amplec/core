from flask import Flask, request, jsonify
import requests, json
from amplec import Amplec
from utils import Logger


app = Flask(__name__)

response_dict = {
    'status': '',
    'message': '',
    'data': {}
}



@app.route('/', methods=['GET'])
def index():
    return "Welcome to the AMPLEC - CORE API"

@app.post('/process')
def process():
    """
    This function implements an API-Endpoint process the submitted data and return the result
    """
    
    resp_dict = response_dict.copy()
   
    submission_id = request.form.get("submission_id")
    regex = request.form.get("regex")
    system_prompt = request.form.get("system_prompt")
     
    missing_params = []
    for key in ['submission_id', 'regex']:
        if locals()[key] is None:
            missing_params.append(key)

    if missing_params != []:
        resp_dict['message'] = f"Missing parameters: {', '.join(missing_params)}"
        resp_dict['status'] = 'error'
        return jsonify(resp_dict), 400
    
    try:
        logger = Logger("console")
        amplec = Amplec(logger, system_prompt)
        resp_dict["message"] = "Processing Worked!"
        resp_dict["status"] = "success"
        resp_dict["data"] = amplec.process(submission_id, regex)
        return jsonify(resp_dict), 200
        
    except Exception as e:
        resp_dict['message'] = str(e)
        resp_dict['status'] = 'error'
        return jsonify(resp_dict), 500


@app.route('/health', methods=['GET'])
def get_health():
    """
    This function will be used as an API-Endpoint to check the health of the API
    """

    return jsonify({'status': 'success', 'message': 'The API is healthy', 'data':{}}), 200
    