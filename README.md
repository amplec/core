# core
This is the core (backend) repo of this project, in here the llm API will be used, as well as the preprocessing done. This module ties all the lose "data" ends together.
Therefore also the interaction with karton will be handled here.
The API this module provides also returns the answers of the llm, for 
For this either the API of an Ollama instance, or the API of OpenAI can be used.
If the user wants to use the OpenAI API, the user has to provide an API key in the settings.

## Installation
The installation of this module should be quite straight forward, as it is a docker container. Before starting however, you need the create a `.env` file in the `src/`-directory. To achieve this, just copy the `template.env` file and rename it to `.env`. Then you can fill in the necessary information.

To start the container, you can use the following command:
```bash
docker compose up -d
```

It has a healthcheck, so you can see if the container is running properly by checking the health-status reported by docker.
This code was only used on Ubuntu based systems, however it should work on other systems as well, if you have `docker` and `docker compose` (the plungin, and not `docker-compose`) installed, aswell as the port `5000` free.

## Usage
This Module depends on a running Karton System with a custom results API, it therefore is not really usable without the other parts. Therefore the usage of this module is not really possible without the other parts of the project.

Nevertheless this module provides an API, which can be used to interact with the system.

## API
This API is used to interact with the LLM and the Karton system. It provides the following endpoints:
### `POST /process`
This endpoint processes the submitted data from a specific **`karton_submission_id`**, returning relevant results from the system.

#### Request Parameters

| **Parameter**          | **Description**                                                                                  | **Required?** |
|------------------------|--------------------------------------------------------------------------------------------------|---------------|
| `karton_submission_id` | The unique submission ID to process from the Karton system                                      | ✅            |
| `regex_or_search`      | The search query or regex pattern to use                                                        | ✅            |
| `use_regex`            | Whether to interpret `regex_or_search` as a regex (`true`/`false`)                               | ✅            |
| `reprocess`            | Re-run the process even if data is cached (`true`/`false`). Default is `false` if not provided. | ❌            |

**All parameters should be sent as form data.**

---

### `POST /chat`
This endpoint allows you to chat with the LLM (Large Language Model). It supports both a normal chat flow and a function-calling flow that references data processed via `/process`.

#### Request Parameters

| **Parameter**       | **Description**                                                                                    | **Required?** |
|---------------------|----------------------------------------------------------------------------------------------------|---------------|
| `system_message`    | A system-level message that sets the overall context or behavior of the LLM                        | ❌            |
| `user_message`      | The user’s message/prompt for the LLM                                                              | ✅            |
| `submission_id`     | An optional submission ID that, if provided, will be used to fetch context from `/process`         | ❌            |
| `reprocess`         | If `true`, triggers a re-processing of data (if any was previously processed)                       | ❌            |
| `function_calling`  | If `true`, enables the LLM to call functions (i.e., fetch data from `/process`) within the session | ❌            |
| `model`             | The model identifier (`llama3.2:3b`, `llama3.1:8b`, `gpt-4o`, `gpt-4o-mini`). Defaults to `llama3.2:latest` if not provided. | ❌ |
| `api_key`           | Required **only if** `model` is set to `gpt-4o` or `gpt-4o-mini`.                                  | Condition-based |

**All parameters should be sent as form data.**
