import requests
from typing import List, Dict, Any
import logging

class EmbeddingClient:
    def __init__(self, base_url: str = "http://0.0.0.0:8000"):
        self.base_url = base_url
        self.logger = logging.getLogger(__name__)

    def update_db(self, 
                 pose_key: str,
                 image_path: str,
                 robot_name: str,
                 timestamp: str,
                 depth_image_path: str,
                 pose: Dict[str, float | int]):
        """
        Update the database with new pose data
        """
        data = {
            "pose_key": pose_key,
            "image_path": image_path,
            "robot_name": robot_name,
            "timestamp": timestamp,
            "depth_image_path": depth_image_path,
            "pose": pose
        }

        try:
            response = requests.post(f"{self.base_url}/update_db", json=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error updating: {str(e)}")
            raise

    def query_db(self, prompts: List[str], limit: int = 10):
        """
        Query the database with prompts
        """
        try:
            response = requests.post(f"{self.base_url}/query_db", 
                                  json={"prompts": prompts, "limit": limit})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error querying: {str(e)}")
            raise

