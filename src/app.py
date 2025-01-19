from flask import Flask, request, jsonify
import requests, json
from amplec import Amplec
from utils import Logger
from chatter import Chatter

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
   
    karton_submission_id = request.form.get("karton_submission_id")
    regex_or_search = request.form.get("regex_or_search")
    use_regex = request.form.get("use_regex")
    if use_regex is not None:
        use_regex = use_regex.lower() in ['true', '1', 't', 'y', 'yes']
    reprocess = request.form.get("reprocess", False) # This is the only optional parameter, where we can set a default value (False)
     
    missing_params = []
    for key in ['karton_submission_id', 'regex_or_search', 'use_regex']:
        if locals()[key] is None:
            missing_params.append(key)

    if missing_params != []:
        resp_dict['message'] = f"Missing parameters: {', '.join(missing_params)}"
        resp_dict['status'] = 'error'
        return jsonify(resp_dict), 400
    
    try:
        logger = Logger("console")
        amplec = Amplec(logger)
        resp_dict["message"] = "Processing Worked!"
        resp_dict["status"] = "success"
        resp_dict["data"] = amplec.generate_llm_data_input_from_submission_id(karton_submission_id, regex_or_search, use_regex, reprocess)
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

@app.route("/chat", methods=["POST"])
def chat():
    """
    This function will be used as an API-Endpoint to chat with the API
    """

    resp_dict = response_dict.copy()
    system_message = request.form.get("system_message")
    user_message = request.form.get("user_message")

    messages_list = [{"role": "system", "content": system_message}, {"role": "user", "content": user_message}]
    
    try:
        logger = Logger("console")
        chat = Chatter(logger, "llama3.2:latest")
        resp_dict['data'] = chat.chat(messages_list)
        resp_dict['message'] = "Chat worked!"
        resp_dict['status'] = "success"
        return jsonify(resp_dict), 200

    except Exception as e:
        resp_dict['message'] = str(e)
        resp_dict['status'] = 'error'
        return jsonify(resp_dict), 500
    