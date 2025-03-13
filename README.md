# Core

This repository contains the **backend** of the project. It provides the core functionality for:
- Tying together various data sources and performing **preprocessing** steps.
- Handling requests via **Karton** (a workflow management and data-processing system).
- Serving a REST API that exposes Large Language Model (LLM) capabilities to other components.

Depending on your configuration, the API can either connect to:
- An **Ollama** instance (local or remote).
- **OpenAI**’s API (if you provide a valid API key).

This core module thus acts as a central hub for data retrieval, transformation, and AI-powered responses.

---

## Table of Contents
1. [Features](#features)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
5. [API Endpoints](#api-endpoints)
   - [POST /process](#post-process)
   - [POST /chat](#post-chat)

---

## Features
- **LLM Integration**: Supports both Ollama and OpenAI models, providing flexibility in deployment.
- **Preprocessing & Data Binding**: Aggregates data from various sources, including Karton, and unifies them before passing to the LLM.
- **Function Calling**: Supports advanced LLM features (e.g., function-calling style requests) to fetch and combine data.
- **Configurable Settings**: Environment variables determine whether the backend connects locally or uses an external service (like OpenAI).

---

## Installation
1. **Clone** this repository:

   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo/core
   ```

2. **Prepare Environment**:
   - Navigate to the `src/` directory.
   - Copy `template.env` to `.env` (rename it) and fill in any required environment variables (e.g., `OPENAI_API_KEY`, `OLLAMA_ENDPOINT`, etc.).

3. **Start with Docker**:
   - In the root directory of this module, run:
     ```bash
     docker compose up -d
     ```
   - The container includes a **healthcheck**, so you can verify if it’s running properly by checking the Docker health status.

> **Note**:  
> - Port `5000` must be available on your system.  
> - This setup was tested on Ubuntu-based systems. It should work elsewhere, assuming you have `docker` and the new `docker compose` plugin installed.

---

## Configuration
Within the `.env` file (in `src/.env`), you can specify:

- **OpenAI or Ollama**: Set the endpoint for Ollama or your OpenAI API key if you want to use OpenAI models.
- **Karton Setup**: Provide any necessary URLs or credentials for connecting to a running Karton system with a custom results API.
- **Miscellaneous**: Configure logging levels, reprocess flags, or other advanced parameters as needed.

Here’s an example snippet (not exhaustive):

```
OPENAI_API_KEY=...
OLLAMA_ENDPOINT=http://ollama-service:11411
KARTON_API_ENDPOINT=http://your-karton-endpoint
LOG_LEVEL=INFO
```

---

## Usage
This module **depends on a running Karton system** with its custom results API. You will typically have:
1. **Karton** handling and dispatching submissions to various workers.
2. **Core** (this module) collecting or preprocessing data and providing an LLM-powered interface.
3. **UI** or other client modules interacting with this core module via the provided API.

Without Karton (and its specific results API), you won’t see meaningful functionality — but for development or testing, you can still call the LLM endpoints directly.

---

## API Endpoints

### `POST /process`
Processes the submitted data for a given **`karton_submission_id`**. After retrieving and optionally preprocessing relevant artifacts from Karton, it returns results that can be further enriched or used by other endpoints.

**Request Parameters (form data)**:

| **Parameter**          | **Description**                                                                                   | **Required?** |
|------------------------|---------------------------------------------------------------------------------------------------|---------------|
| `karton_submission_id` | The unique submission ID from the Karton system.                                                 | ✅            |
| `regex_or_search`      | The text query or regex pattern to look for in the data.                                          | ✅            |
| `use_regex`            | Interpret `regex_or_search` as regex (`true`/`false`).                                            | ✅            |
| `reprocess`            | Force reprocessing (`true`/`false`). Defaults to `false` if not set.                              | ❌            |

**Example**:
```bash
curl -X POST http://localhost:5000/process \
  -F 'karton_submission_id=abc123' \
  -F 'regex_or_search=password' \
  -F 'use_regex=false'
```

---

### `POST /chat`
Enables conversation with the LLM. You can supply a normal user prompt or leverage **function-calling** to fetch processed data from `/process` on the fly.

**Request Parameters (form data)**:

| **Parameter**       | **Description**                                                                                          | **Required?** |
|---------------------|----------------------------------------------------------------------------------------------------------|---------------|
| `system_message`    | A high-level “system” message that sets context or instructions for the LLM.                             | ❌            |
| `user_message`      | The user’s direct prompt or query to the LLM.                                                            | ✅            |
| `submission_id`     | An optional submission ID (links to processed data from `/process`).                                     | ❌            |
| `reprocess`         | If `true`, triggers re-processing (if data was previously cached).                                       | ❌            |
| `function_calling`  | If `true`, allows the LLM to automatically retrieve data via function calls (linked to `/process`).       | ❌            |
| `model`             | Specify the model ID to use (`llama3.2:3b`, `llama3.1:8b`, `gpt-4o`, `gpt-4o-mini`). Defaults to `llama3.2:latest`. | ❌ |
| `api_key`           | **Required** only if using `gpt-4o` or `gpt-4o-mini`.                                                    | Based on Model |

**Example**:
```bash
curl -X POST http://localhost:5000/chat \
  -F 'user_message="Summarize any relevant threat intel for submission_id xyz"' \
  -F 'submission_id=xyz' \
  -F 'function_calling=true'
```

