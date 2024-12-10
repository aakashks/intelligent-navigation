import asyncio
import re
from typing import Dict, List, Optional, Union
from icecream import ic
from vlm import run_image_queries


def run_clip_on_objects(object_list, client, topk=5):  
    prompt = [f'a photo of a {obj}' for obj in object_list]  
    results = client.query_db(prompts=prompt, limit=topk)
    ic(results)

    object_detections = {}  
    for i in range(len(object_list)):  
        # Store all metadata for each result  
        result_metadatas = []
        
        for metadata in results['metadatas'][i]:  
            result_metadatas.append(metadata)  

        object_detections[i] = {  
            'object': object_list[i],   
            'results': result_metadatas  
        }  

    ic(object_detections)  
    return object_detections  




def extract_points(text: str) -> Optional[Dict[str, Union[List[float], str]]]:
    """
    Extract coordinates and messages from point/points XML-like tags.
    Handles both single coordinates (x="10.5") and multiple coordinates (x1="10.5" x2="9").
    Returns all valid coordinate pairs even if some coordinates are missing.

    Args:
        text: Input text containing point/points tags

    Returns:
        Dictionary containing coordinates and messages, or None if no match
    """
    # Match either <point> or <points> tags
    pattern = r'<point(?:s)?([^>]*)>(.*?)</point(?:s)?>'
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    attributes = match.group(1)
    main_message = match.group(2).strip()

    # Initialize dictionaries for coordinates
    x_dict = {}
    y_dict = {}
    alt_message = None

    try:
        # Extract x coordinates (both x="val" and x1="val", x2="val" formats)
        x_matches = re.finditer(r'x(\d*)="([^"]*)"', attributes)
        for x_match in x_matches:
            index = x_match.group(1) if x_match.group(1) else '1'
            x_dict[int(index)] = float(x_match.group(2))

        # Extract y coordinates (both y="val" and y1="val", y2="val" formats)
        y_matches = re.finditer(r'y(\d*)="([^"]*)"', attributes)
        for y_match in y_matches:
            index = y_match.group(1) if y_match.group(1) else '1'
            y_dict[int(index)] = float(y_match.group(2))

        # Extract alt message
        alt_match = re.search(r'alt="([^"]*)"', attributes)
        if alt_match:
            alt_message = alt_match.group(1)

    except ValueError as e:
        print(f"Error parsing coordinates: {e}")
        return None

    # Find valid coordinate pairs
    x_coords = []
    y_coords = []

    # Get all indices that have both x and y coordinates
    valid_indices = sorted(set(x_dict.keys()) & set(y_dict.keys()))

    for idx in valid_indices:
        x_coords.append(x_dict[idx])
        y_coords.append(y_dict[idx])

    if not x_coords or not y_coords:
        print("Error: No valid coordinate pairs found")
        return None

    return {
        "image_x": x_coords,
        "image_y": y_coords,
        # "alt_message": alt_message,
        # "main_message": main_message,
    }


def run_vlm(user_query, object_detections, concurrent_requests=50, timeout=240):  
    coord_data = {}  

    for i, data in object_detections.items():  
        template = 'User has asked the robot - "{user_query}". Point to the {object_name} in the image that will fulfill the user query.'
        prompt = template.format(user_query=user_query, object_name=data['object'])

        image_b64_lst = [result['image_b64'] for result in data['results']]

        ic(prompt)

        vlm_results = asyncio.run(  
            run_image_queries(  
                images_b64=image_b64_lst,   
                prompts=prompt,   
                timeout=timeout,   
                concurrent_requests=concurrent_requests  
            )  
        )  
        ic(vlm_results)  

        coord_data[i] = {  
            'object': data['object'],  
            'points': []  
        }  

        for vlm_result, metadata in zip(vlm_results, data['results']):  
            points = extract_points(vlm_result)  
            if points:  
                # Combine points with metadata  
                point_data = {  
                    **points,  
                    **metadata,
                }  
                ic(point_data)
                assert 'image_path' in point_data, "Image path not found in metadata"
                assert 'pose_key' in point_data, "Pose key not found in metadata"
                # assert 'pose_x' in point_data, "Pose x not found in metadata"
                # assert 'pose_y' in point_data, "Pose y not found in metadata"
                coord_data[i]['points'].append(point_data)  

    return coord_data  