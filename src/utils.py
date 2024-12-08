from PIL import Image, ImageDraw
import os
from icecream import ic

def get_count_from_coord_data(coord_data):
    """
    Get the total count of objects from the given coordinate data.
    """
    count = 0
    for obj_id in coord_data:
        obj_data = coord_data[obj_id]
        count += len(obj_data["points"])
        
    return count

def display_coord_data(coord_data):
    """
    Get the total count of objects from the given coordinate data.
    """
    displayable_coord_data = coord_data.copy()
    
    for obj_id in coord_data:
        for data in coord_data[obj_id]["points"]:
            data.pop("depth_image_path", None)
            data.pop('image_b64', None)
        
    return displayable_coord_data        


def get_topk_imgs_from_coord_data(coord_data, k=4):
    """
    Retrieve the top-k object images from the given coordinate data.
    Draws a red point at the specified coordinates.
    """
    # Extract all (object, path) pairs from nested structure
    path_pairs = []
    for obj_id in coord_data:
        obj_data = coord_data[obj_id]
        object_name = obj_data["object"]
        # Add all paths for this object
        for point_data in obj_data["points"]:
            img = Image.open(point_data["image_path"])
            draw = ImageDraw.Draw(img)
            
            # Get image dimensions to scale coordinates
            width, height = img.size
            
            # Draw red dots at each coordinate pair
            for x, y in zip(point_data["image_x"], point_data["image_y"]):
                # Convert percentage to actual pixels
                pixel_x = int(x * width / 100)
                pixel_y = int(y * height / 100)
                
                # Draw red circle with radius 5
                draw.ellipse(
                    [(pixel_x-5, pixel_y-5), (pixel_x+5, pixel_y+5)],
                    fill='red',
                    outline='red'
                )
            
            path_pairs.append((object_name, img))
            
    # Return only top k pairs (they're already sorted by confidence)
    return path_pairs[:k]


def get_topk_paths_from_coord_data(coord_data, k=4):
    """
    Retrieve the top-k object paths from the given coordinate data.
    """
    # Extract all (object, path) pairs from nested structure
    path_pairs = []
    for obj_id in coord_data:
        obj_data = coord_data[obj_id]
        object_name = obj_data["object"]
        # Add all paths for this object
        for point_data in obj_data["points"]:
            img_path = point_data["image_path"]
            path_pairs.append((object_name, img_path))
            
    # Return only top k pairs (they're already sorted by confidence)
    return path_pairs[:k]


# # Sample coordinate data
# coord_data = {
#     0: {
#         "object": "bed",
#         "points": [
#             {
#                 "image_x": [49.8],
#                 "image_y": [32.3],
#                 "image_path": "/home/user1/s_ws/images/10.png",
#                 "pose_key": "node_1_23",
#                 "robot_name": "robot_1",
#                 "timestamp": "2022-01-01_12:00:00",
#                 "depth_image_path": "/home/user1/s_ws/depth/10.png",
#                 "pose_x": 2.4,
#                 "pose_y": 3.5,
#                 "pose_z": 1.2,
#                 "pose_w": 0.9
#             },
#             {
#                 "image_x": [48.9],
#                 "image_y": [35.4],
#                 "image_path": "/home/user1/s_ws/images/11.png",
#                 "pose_key": "node_1_29",
#                 "robot_name": "robot_6",
#                 "timestamp": "2022-01-01_10:00:00",
#                 "depth_image_path": "/home/user1/s_ws/depth/11.png",
#                 "pose_x": 2.4,
#                 "pose_y": 3.5,
#                 "pose_z": 1.2,
#                 "pose_w": 0.9
#             }
#         ]
#     },
# }