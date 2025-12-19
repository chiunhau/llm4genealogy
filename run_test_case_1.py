import os
import base64
from openai import OpenAI
import httpx
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://ai-gateway.vercel.sh/v1",
    api_key=os.environ.get("VERCEL_AI_GATEWAY_KEY"),
)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def process_image_and_text(text_prompt, image_input):
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
            # max_tokens=300,
        )
        
        print(response.choices[0].message.content)
        return response.choices[0].message.content

    except Exception as e:
        print(f"An error occurred: {e}")
        return "ERROR"

if __name__ == "__main__":
    import glob
    import csv
    import time
    
    # Directories - relative to this script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    TEST_CASES_DIR = os.path.join(SCRIPT_DIR, "test_cases/1")
    IMAGES_DIR = os.path.join(SCRIPT_DIR, "data/family_trees_png")
    RESULTS_DIR = os.path.join(SCRIPT_DIR, "test_results/1")
    
    # Ensure results directory exists
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # Get all CSV test cases
    test_case_files = glob.glob(os.path.join(TEST_CASES_DIR, "*.csv"))
    
    print(f"Found {len(test_case_files)} test case files.")
    
    for csv_file in test_case_files:
        filename = os.path.basename(csv_file)
        
        # Check if output already exists
        output_file = os.path.join(RESULTS_DIR, filename)
        if os.path.exists(output_file):
            print(f"Skipping {filename} because results already exist.")
            continue

        image_filename = filename.replace(".csv", ".png")
        image_path = os.path.join(IMAGES_DIR, image_filename)
        
        if not os.path.exists(image_path):
            print(f"Image not found for {filename}: {image_path}")
            continue
            
        print(f"Processing {filename} with image {image_filename}...")
        
        results = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            for row in rows:
                person_a = row['person_a']
                person_b = row['person_b']
                
                prompt_text = f"""
      Context: This is a Chinese family tree. 
      
      Task: Please answer what is the relationship between {person_a} (Person A) and {person_b} (Person B) ?
      
      Note: 
      - Answer in the form of "Person A is Person B's [relationship]" but return only the relationship.
      - Only reply the relationship as either CHILD, SPOUSE, PARENT, SIBLING, GRANDCHILD, GRANDPARENT, GREAT_GRANDCHILD, GREAT_GRANDPARENT, UNCLE_OR_AUNT, NEPHEW_OR_NIECE, COUSIN.
      - If you can not find the persons in the family tree, just reply "NOT_FOUND"
      - If you find the relationship but not sure, reply "OTHER"
                """
                
                print(f"  Querying: {person_a} -> {person_b}")
                llm_response = process_image_and_text(prompt_text, image_path)
                
                # Check for rate limits or errors, maybe sleep a bit?
                # time.sleep(1) 
                
                row['llm_prediction'] = llm_response.strip() if llm_response else "ERROR"
                results.append(row)
        
        # Save results
        output_file = os.path.join(RESULTS_DIR, filename)
        if results:
            fieldnames = list(results[0].keys())
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)
                
        print(f"Saved results to {output_file}")
