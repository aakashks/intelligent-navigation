# Interactive Object Search From Swarm Feed

## Prerequisites

Before setting up the application, ensure that your system meets the following requirements:

- **Python 3.10+**
- **Minimum GPU Requirement:** 16 GB GPU memory (NVIDIA recommended)

## Setup

Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
```

## Instructions to Run

The application requires a GPU with a minimum of 16GB VRAM. If a suitable local GPU is unavailable, you can offload GPU-intensive tasks to a remote server or cloud service, while running the Streamlit app locally.

#### Chromadb Vector DB Embedding API

The embedding API is built using FastAPI and Uvicorn, and it calculates and stores image embeddings for efficient object search. Start the vector database server to handle the embedding calculations and allow API queries by running the following command:

To start the vector database server that calculates and stores image embeddings and enables API to query the images, run the following command:

```bash
python db_server.py .chromadb/ --port 8000
```

#### vLLM

To serve the vision language model that will be used to find objects in the environment, run the following command:

```bash
vllm serve allenai/Molmo-7B-D-0924 --task generate \
  --trust-remote-code --max-model-len 4096 --dtype bfloat16 --port 8080

```

#### .env file

Set your openai API key in the `.env` file. 

Note that if you are running the vllm and chromadb on a different machine, you need to set the `DB_URL` and `VLLM_URL` environment variables in the `.env` file.
To make images available to the embeddings API, you need to mount the server's file system to the simulation machine.

To mount the server's file system to the simulation machine, you can use `sshfs`:
```bash
sshfs <username>@<ip_address>:/path/to/remote /path/to/mount
```

You must set `DATA_DIR` and `MOUNT_DIR` environment variables in the `.env` file.

An example `.env` file is shown below:

```bash
DB_URL=http://<ip_address>:8000
VLLM_URL=http://<ip_address>:8080
DATA_DIR=/path/to/remote
MOUNT_DIR=/path/to/mount
OPENAI_API_KEY=<your_openai_api_key>
```

#### Starting the Streamlit App

To start the Streamlit app, run the following command:

```bash
streamlit run app.py
```
