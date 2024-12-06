import os
import requests
import json
import re
from pydantic import BaseModel
from typing import List

from icecream import ic

# Define a Pydantic model for the expected JSON response
class PossibleObjects(BaseModel):
    possible_objects: List[str]


def ask_text_query(
    text_prompt,
    model_name="gpt-4o-mini",
    api_base="https://api.openai.com/v1",
    timeout=10,
):
    """
    Sends a text prompt to the OpenAI API and returns the response.
    """
    try:
        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": text_prompt}],
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        }

        response = requests.post(
            f"{api_base}/chat/completions",
            json=payload,
            headers=headers,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        output = data["choices"][0]["message"]["content"]

    except Exception as e:
        output = f"Error: {str(e)}"

    return output

def postprocess_llm(response):
    """
    Extracts the JSON part from the assistant's response.
    """
    try:
        json_string = re.search(r"```json\n(.*?)\n```", response, re.DOTALL).group(1)
        return PossibleObjects(**json.loads(json_string))
    except AttributeError:
        raise ValueError("The response does not contain a valid JSON block.")
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format in the response.")
    

def get_possible_objects(prompt):
    # unless we get correct json output keep prompting
    # try 5 times
    final_prompt = (
            f"""
Given is user query: "{prompt}".
{os.getenv('ENV_PROMPT', "We are currently in an indoor environment that can be a warehouse, office, factory, or a hospital.")}
Commands are given to a robot to navigate the environment.
Which objects or entities could the user be referring to when they say "{prompt}"? 
The robot would then need to go to that object or entity.
Remember that the robot should be able to go to the possible object and then perform an action suitable to the user query.
Return at most 4 such objects. Make sure the first object is the most probable one.
Return the possible objects in a JSON format.
"""
            + """
Eg. if the query is "go upstairs", the possible objects could be "stairs", "staircase", "steps". Hence the JSON output would be:
{
    "possible_objects": [
        "stairs",
        "staircase",
        "steps"
    ]
}
"""
        )
    count = 0
    while True:
        response = ask_text_query(final_prompt)
        try:
            objects = postprocess_llm(response)
            return objects.model_dump()
        except ValueError as ve:
            ic(f"Failed to parse response: {ve}")
            ic(response)
            if count < 5:
                count += 1
                ic(f"Retrying... Attempt {count}")
            else:
                ic("Failed to get a valid response from the model.")
                break
            
    return None


