import asyncio
import aiohttp
import pandas as pd
import json
from tqdm.asyncio import tqdm_asyncio
import os
import gc
import sys
import base64

async def fetch(session, semaphore, prompt, image_url):
    """
    Asynchronously fetch the API response for a single image.
    """
    async with semaphore:
        try:
            payload = {
                "model": "allenai/Molmo-7B-D-0924",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }],
            }

            headers = {
                "Authorization": f"Bearer EMPTY",
                "Content-Type": "application/json",
            }

            # Set a specific timeout for the request
            request_timeout = aiohttp.ClientTimeout(total=None)   # timeout for each request (note that all requests were sent simultaneously)

            async with session.post(f"{os.getenv('VLLM_URL', 'http://localhost:8080')}/v1/chat/completions", json=payload, headers=headers, timeout=request_timeout) as response:
                if response.status == 200:
                    data = await response.json()
                    # Adjust based on actual response structure
                    vlm_output = data['choices'][0]['message']['content']
                else:
                    vlm_output = f"Error: {response.status}"
        except asyncio.TimeoutError:
            vlm_output = "Timeout Error: Request took longer"
        except Exception as e:
            vlm_output = f"Exception: {str(e)}"

        return vlm_output
    
    
async def run_on_image(session, semaphore, prompt, image_path):
    # convert image to base64
    # image_path = image_path.replace("/home/ps2-mid", os.getenv('MOUNT_DIR'))
    with open(image_path, 'rb') as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
        
    base64_image = "data:image/jpeg;base64," + base64_image
    # file_path_image = 'file://' + image_path
    
    return await fetch(session, semaphore, prompt, base64_image)


async def run_multiple_image_query(image_paths, prompts, timeout, concurrent_requests):
    """
    Main asynchronous function to process all images.
    """
    semaphore = asyncio.Semaphore(concurrent_requests)
    connector = aiohttp.TCPConnector(limit=concurrent_requests)
    timeout = aiohttp.ClientTimeout(total=timeout)  # Adjust timeout as needed

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

        tasks = []
        for image_path, prompt in zip(image_paths, prompts):
            tasks.append(run_on_image(session, semaphore, prompt, image_path))
        
        results = await asyncio.gather(*tasks)

        gc.collect()
        
    with open("results.json", "a") as f:
        json.dump(results, f)
        
    return results

async def run_multiple_image_query_same_prompt(image_paths, prompt, timeout, concurrent_requests):
    """
    Main asynchronous function to process all images.
    """
    semaphore = asyncio.Semaphore(concurrent_requests)
    connector = aiohttp.TCPConnector(limit=concurrent_requests)
    timeout = aiohttp.ClientTimeout(total=timeout)  # Adjust timeout as needed

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

        tasks = []
        for image_path in image_paths:
            tasks.append(run_on_image(session, semaphore, prompt, image_path))
        
        results = await asyncio.gather(*tasks)

        gc.collect()
        
    with open("results.json", "a") as f:
        json.dump(results, f)
        
    return results

