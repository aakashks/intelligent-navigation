# Interactive Object Search From Swarm Feed

## Prerequisites

Before setting up the application, ensure that your system meets the following requirements:

- **Python 3.10+**
- **Minimum GPU Requirement:** 16 GB GPU memory (NVIDIA recommended)

## Setup

### Environment Variables

Create a `.env` file in the root directory of the project to store your configuration variables securely. This file should include API keys and URLs for services if they are running on different machines. Make sure to not commit this file to version control.
Populate the `.env` file with the following variables:

```env
DB_URL=http://<db_server_ip>:8000
VLLM_URL=http://<vllm_server_ip>:8080
DATA_DIR=/path/to/local/data
OPENAI_API_KEY=your_openai_api_key
```

- `DB_URL`: URL where the Chromadb embedding API is hosted.
- `VLLM_URL`: URL where the vLLM server is hosted.
- `DATA_DIR`: Directory path on the local machine where the data will be stored.
- `OPENAI_API_KEY`: Your OpenAI API key for accessing language models.

## Running the Services (on the Remote Server)

Ensure that each service is running in its own terminal or consider using a process manager like `tmux`, `screen`, or `docker-compose` for managing multiple services.

### Chromadb Vector Database Embedding API

The embedding API is a custom-built service using FastAPI and Uvicorn. It calculates and stores image embeddings and provides an API to query images based on these embeddings.

**Fix Chromadb Bug:**

Before starting the embedding API server, run the following script to fix known bugs in chromadb library:

```bash
python fix_chromadb_bug.py
```

**Start the Embedding API Server:**

```bash
cd /path/to/remote/data
# make sure to copy the db_server.py file to the data directory
python db_server.py . --port 8000
```

- `/path/to/remote/data/` is the directory where Chromadb will store its data on the remote server.

### vLLM Vision Language Model Server

The vLLM server hosts the vision-language model responsible for interpreting and generating responses based on visual input.

**Start the vLLM Server:**

```bash
vllm serve allenai/Molmo-7B-D-0924 --task generate --trust-remote-code --max-model-len 4096 --dtype bfloat16 --port 8080
```

**Notes:**

- `allenai/Molmo-7B-D-0924` specifies the vision language model to use.
- Ensure that the server has at least 16 GB of GPU memory available.
- Adjust the `--port` if necessary to avoid conflicts.

### Streamlit Application

The Streamlit app provides an interactive frontend for users to perform object searches.

**Start the Streamlit App:**

```bash
streamlit run app.py
```

**Notes:**

- By default, Streamlit runs on `http://localhost:8501`. You can specify a different port using the `--server.port` flag if needed.
- The app will interact with both the Chromadb embedding API and the vLLM server as configured in the `.env` file.
