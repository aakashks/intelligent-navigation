import argparse
import base64
import logging
import os
from typing import Dict, List, Optional, cast

import chromadb
import uvicorn
from chromadb.api.types import (
    Document,
    Embedding,
    Image,
)
from chromadb.utils.data_loaders import ImageLoader
from chromadb.utils.embedding_functions import OpenCLIPEmbeddingFunction
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# monkey patching to fix cuda device bug in chromadb
class OpenCLIPEmbeddingFunctionFixed(OpenCLIPEmbeddingFunction):
    def __init__(self, model_name, checkpoint, device='cpu'):
        super().__init__(model_name, checkpoint, device)
        self._device = device
        self._model = self._model.to(device)

    def _encode_image(self, image: Image) -> Embedding:
        pil_image = self._PILImage.fromarray(image)
        with self._torch.no_grad():
            image_features = self._model.encode_image(
                self._preprocess(pil_image).unsqueeze(0).to(self._device)
            )
            image_features /= image_features.norm(dim=-1, keepdim=True)
            return cast(Embedding, image_features.squeeze().cpu().numpy())
    
    def _encode_text(self, text: Document) -> Embedding:
        with self._torch.no_grad():
            text_features = self._model.encode_text(self._tokenizer(text).to(self._device))
            text_features /= text_features.norm(dim=-1, keepdim=True)
            return cast(Embedding, text_features.squeeze().cpu().numpy())


# Setup argument parser
parser = argparse.ArgumentParser(description='FastAPI server with ChromaDB')
parser.add_argument('path', type=str,
                   help='Path for persistent storage')
parser.add_argument('--name', default='clip_embeddings', type=str,
                   help='Name of the ChromaDB collection')
parser.add_argument('--port', type=int, default=8000,
                   help='Port number for the FastAPI server')

args = parser.parse_args()

app = FastAPI()

# Initialize ChromaDB and embedding function
client = chromadb.PersistentClient(os.path.join(args.path, '.chromadb'))
embedding_function = OpenCLIPEmbeddingFunctionFixed('ViT-B-16-SigLIP', 'webli', device='cuda')
db_collection = client.get_or_create_collection(
    name=args.name, 
    embedding_function=embedding_function, 
    data_loader=ImageLoader()
)

class PoseData(BaseModel):
    pose_key: str
    image_path: str
    image_b64: str
    robot_name: str
    timestamp: str
    depth_image_path: str
    pose: Dict[str, float | int]

class QueryRequest(BaseModel):
    prompts: List[str]
    limit: Optional[int] = 5

def flatten_metadata(data: PoseData) -> Dict:
    """Flatten the pose dictionary into individual metadata fields"""
    metadata = {
        "pose_key": data.pose_key,
        "image_path": data.image_path,
        "image_b64": data.image_b64,
        "robot_name": data.robot_name,
        "timestamp": data.timestamp,
        "depth_image_path": data.depth_image_path,
        "pose_x": data.pose.get("x", 0.0),
        "pose_y": data.pose.get("y", 0.0),
        "pose_z": data.pose.get("z", 0.0),
        "pose_w": data.pose.get("w", 0.0)
    }
    return metadata

@app.post("/update_db")
async def update_db(data: PoseData):
    try:
        # Check if record exists
        existing_record = db_collection.get(ids=[data.pose_key])

        # Flatten the metadata
        metadata = flatten_metadata(data)
        
        remote_image_path = os.path.join(args.path, 'images/', f"{data.pose_key}.jpg")
        print(f"Saving image to {remote_image_path}")
        
        # Save the image to disk
        logger.info(f"Saving image to {remote_image_path}")
        try:  
            with open(remote_image_path, 'wb') as image_file:  
                image_file.write(base64.b64decode(data.image_b64))  
        except Exception as e:  
            logger.error(f"Failed to save image: {str(e)}")  
            raise HTTPException(status_code=400, detail="Invalid base64 image data")  


        if existing_record['ids']:
            logger.info(f"Updating record for pose {data.pose_key}")
            db_collection.update(
                ids=data.pose_key,
                uris=remote_image_path,
                metadatas=metadata
            )
        else:
            logger.info(f"Adding new record for pose {data.pose_key}")
            db_collection.add(
                ids=data.pose_key,
                uris=remote_image_path,
                metadatas=metadata
            )

        return {"message": "Database updated successfully"}

    except Exception as e:
        logger.error(f"Error updating: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query_db")
async def query_db(request: QueryRequest):
    try:
        results = db_collection.query(
            query_texts=request.prompts,
            n_results=request.limit  # Fixed parameter name from n_limits to n_results
        )
        return results

    except Exception as e:
        logger.error(f"Error querying: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=args.port)
    os.makedirs(os.path.join(args.path, 'images'), exist_ok=True)
