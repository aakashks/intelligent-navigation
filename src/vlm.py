import asyncio
import aiohttp
import base64
import json
import os
import gc

async def fetch(session, semaphore, prompt, image_data):
    """
    Asynchronously fetch the API response for a single image.  

    Args:  
        session (aiohttp.ClientSession): The HTTP session for making requests.  
        semaphore (asyncio.Semaphore): Semaphore to limit concurrent requests.  
        prompt (str): The text prompt to send to the API.  
        image_data (str): The image data (either URL or base64-encoded string).  

    Returns:  
        str: The API response or an error message.  
    """
    async with semaphore:
        try:
            payload = {
                "model": "allenai/Molmo-7B-D-0924",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_data}},
                    ],
                }],
            }

            headers = {
                "Authorization": f"Bearer {os.getenv('VLLM_API_KEY', 'EMPTY')}",
                "Content-Type": "application/json",
            }

            async with session.post(  
                f"{os.getenv('VLLM_URL', 'http://localhost:8080')}/v1/chat/completions",  
                json=payload,  
                headers=headers  
            ) as response:  
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content']
                else:
                    return f"Error: {response.status} - {await response.text()}"
        except asyncio.TimeoutError:
            return "Timeout Error: Request took too long"
        except Exception as e:
            return f"Exception: {str(e)}"


def encode_image_to_base64(image_path):  
    """  
    Encodes an image file to a base64 string.  

    Args:  
        image_path (str): Path to the image file.  

    Returns:  
        str: Base64-encoded image string.  
    """  
    with open(image_path, 'rb') as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{base64_image}"


async def process_images(session, semaphore, prompts, image_data_list):  
    """  
    Processes multiple images asynchronously.  

    Args:  
        session (aiohttp.ClientSession): The HTTP session for making requests.  
        semaphore (asyncio.Semaphore): Semaphore to limit concurrent requests.  
        prompts (list or str): List of prompts or a single prompt for all images.  
        image_data_list (list): List of image data (URLs or base64 strings).  

    Returns:  
        list: List of API responses for each image.  
    """  
    tasks = []
    if isinstance(prompts, str):
        prompts = [prompts] * len(image_data_list)  # Use the same prompt for all images  

    for prompt, image_data in zip(prompts, image_data_list):
        tasks.append(fetch(session, semaphore, prompt, image_data))  

    return await asyncio.gather(*tasks)


async def run_image_queries(image_paths=None, images_b64=None, prompts=None, timeout=240, concurrent_requests=10):  
    """  
    Main function to process multiple image queries asynchronously.  

    Args:  
        image_paths (list, optional): List of image file paths.  
        images_b64 (list, optional): List of base64-encoded image strings.  
        prompts (list or str): List of prompts or a single prompt for all images.  
        timeout (int, optional): Timeout for each request in seconds. Defaults to 60.  
        concurrent_requests (int, optional): Maximum number of concurrent requests. Defaults to 5.  

    Returns:  
        list: List of API responses for each image.  
    """  
    if not (image_paths or images_b64):  
        raise ValueError("Either 'image_paths' or 'images_b64' must be provided.")  

    # Convert image paths to base64 if provided  
    if image_paths:  
        images_b64 = [encode_image_to_base64(path) for path in image_paths]  

    semaphore = asyncio.Semaphore(concurrent_requests)
    connector = aiohttp.TCPConnector(limit=concurrent_requests)
    client_timeout = aiohttp.ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(connector=connector, timeout=client_timeout) as session:
        results = await process_images(session, semaphore, prompts, images_b64)

    # Save results to a file  
    with open("vlm_results.json", "a") as f:
        json.dump(results, f)

    gc.collect()
    
    return results

