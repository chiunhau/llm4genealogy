import os
import base64
import json
from openai import OpenAI
import httpx
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://ai-gateway.vercel.sh/v1",
    api_key=os.environ.get("VERCEL_AI_GATEWAY_KEY"),
)

def encode_image(image_path):
    """Encodes a local image file to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_image_and_text(text_prompt, image_input):
    """
    Sends a text prompt and an image (URL or local path) to the model.
    """
    
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": text_prompt},
            ],
        }
    ]

    try:
        base64_image = encode_image(image_input)
        image_content = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}" # Adjust mime type if needed (png, etc.)
            },
        }
    except Exception as e:
        print(f"Error reading image file: {e}")
        return

    messages[0]["content"].append(image_content)

    try:
        response = client.chat.completions.create(
            model="google/gemini-3-flash", 
            messages=messages,
            max_tokens=1024,
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"An error occurred: {e}")
        return "ERROR"

if __name__ == "__main__":
    import glob
    import time
    
    # Directories - relative to this script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    TEST_CASES_DIR = os.path.join(SCRIPT_DIR, "test_cases/2")
    IMAGES_DIR = os.path.join(SCRIPT_DIR, "data/family_trees_png")
    RESULTS_DIR = os.path.join(SCRIPT_DIR, "test_results/2")
    
    # Ensure results directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Target specific file as per original run_tests.py, or all if needed.
    # Matching original run_tests.py behavior of specific target for now.
    test_case_files = glob.glob(os.path.join(TEST_CASES_DIR, "*.json"))
    
    print(f"Found {len(test_case_files)} test case files.")
    
    for json_file in test_case_files:
        filename = os.path.basename(json_file)
        
        # Check if output already exists
        output_file = os.path.join(RESULTS_DIR, filename)
        if os.path.exists(output_file):
            print(f"Skipping {filename} because results already exist.")
            continue

        image_filename = filename.replace(".json", ".png")
        image_path = os.path.join(IMAGES_DIR, image_filename)
        
        if not os.path.exists(image_path):
            print(f"Image not found for {filename}: {image_path}")
            continue
            
        print(f"Processing {filename} with image {image_filename}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
            
        results = []
        
        for case in test_cases:
            person_b = case['person_b']
            relationship = case['relationship_type']
            
            prompt_text = f"""
      Context: This is a Chinese family tree. 
      
      Task: Please answer who are ALL the {relationship} of {person_b} (Person B)? Answer with a simple comma-separated list of names, e.g. "Name1, Name2".
      
      Note: 
      - If there is only one, just return the name, e.g. "Name1".
      - If you can not find any persons, reply "NOT_FOUND".
      - Do not include any other text or markdown formatting.
            """
            
            print(f"  Querying: ? ({relationship}) -> {person_b}")
            llm_response = process_image_and_text(prompt_text, image_path)
            
            case['llm_prediction'] = llm_response.strip() if llm_response else "ERROR"
            results.append(case)
        
        # Save results
        output_file = os.path.join(RESULTS_DIR, filename)
        if results:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
        print(f"Saved results to {output_file}")
