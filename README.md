# Interactive Object Search From Swarm Feed

## Setup

To install the required dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Running

#### Chromadb Vector DB

To start the vector database server that calculates and stores image embeddings and enables API to query the images, run the following command:

```bash
python db_server.py .chromadb/ --port 8000
```

You must set the environment variable `DB_URL` to the URL of the running server.

#### vLLM Server

To serve the vision language model that will be used to find objects in the environment, run the following command:

```bash
vllm serve allenai/Molmo-7B-D-0924 --task generate \
  --trust-remote-code --max-model-len 4096 --dtype bfloat16 --port 8080

```

You must set the environment variable `VLLM_URL` to the URL of the running server.

#### .env file

Create a `.env` file with the following content:

```bash
DB_URL=http://<ip_address>:8000
VLLM_URL=http://<ip_address>:8080
OPENAI_API_KEY=<your_openai_api_key>
```

Note that if you are running the simulation on a different machine, you can mount the server's file system to the simulation machine using `sshfs`.
This is necessary to save the images and depth data to the server. You'd have to set the `DATA_DIR` and `MOUNT_DIR` environment variables in the `.env` file.
