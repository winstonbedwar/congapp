# --- PYTHON PREREQUISITES ---
# This script requires the following packages installed:
# pip install requests
# pip install slugify
# pip install cerebras-cloud
# -----------------------------

import requests
import time
import json
import logging
import os
from slugify import slugify
from typing import Union
# Import the necessary Cerebras SDK components
from cerebras.cloud.sdk import Cerebras 

# Configure basic logging for visibility and easy debugging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(asctime)s - %(message)s', datefmt='%H:%M:%S')

# --- LLM API Configuration ---
# NOTE: The provided key is used here for the Cerebras API access.
CEREBRAL_API_KEY = "csk-yc3nryechcj9hp2etk44yffvwk6eetc4863eee3924n62fkw" 
# Use the model requested by the user
CEREBRAL_MODEL = "llama-4-scout-17b-16e-instruct" 

# Initialize the Cerebras Client globally using the provided key
try:
    # In a typical environment, you would use os.environ.get("CEREBRAS_API_KEY")
    # Here, we hardcode the provided key for the Canvas environment setup
    CEREBRAS_CLIENT = Cerebras(api_key=CEREBRAL_API_KEY)
    logging.info("Cerebras SDK Client initialized successfully.")
except Exception as e:
    logging.error(f"Failed to initialize Cerebras Client: {e}")
    CEREBRAS_CLIENT = None

# --- Firebase Configuration ---
FIREBASE_DATABASE_URL = "https://orwell-ea558-default-rtdb.firebaseio.com"
# Note: This is a placeholder key required for the Firebase REST calls below
FIREBASE_API_KEY = "AIzaSyCS07UgX2GnmuufEQET-RYOtm8i0XaZkWk" 

# Firebase Database Paths
DATABASE_ROOT_PATH = 'congress/bills' 
QUIZ_ROOT_PATH = 'quizzes'   


# --- Utility Functions (Used only for Firebase HTTP calls) ---

def fetch_with_backoff(url: str, retries: int = 5, delay: int = 1, method: str = 'GET', data: Union[dict, None] = None, log_context: str = "Request") -> Union[requests.Response, None]:
    """Robust fetch using requests with exponential backoff for Firebase operations."""
    for i in range(retries):
        try:
            headers = {'Content-Type': 'application/json'} 
            
            if method == 'GET':
                response = requests.get(url, timeout=15)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, timeout=15, headers=headers)
            else:
                raise ValueError("Unsupported HTTP method.")

            # Simple rate limit handling for Firebase/general HTTP
            if response.status_code == 429 and i < retries - 1:
                logging.warning(f"[{log_context}] Rate limit hit. Retrying in {delay * (2 ** i)}s...")
                time.sleep(delay * (2 ** i))
                continue
            
            response.raise_for_status() 
            return response
            
        except requests.exceptions.RequestException as error:
            wait_time = delay * (2 ** i)
            logging.error(f"[{log_context}] HTTP/Network Failure (Attempt {i+1}). Error: {error}. Status: {response.status_code if 'response' in locals() else 'N/A'}")
            
            if i == retries - 1:
                logging.error(f"[{log_context}] FINAL FAILURE: Failed after {retries} retries.")
                return None
            
            time.sleep(wait_time)
            
    return None

def get_firebase_data(path: str) -> Union[requests.Response, None]:
    """Fetches data from the Firebase Realtime Database REST API."""
    full_url = f"{FIREBASE_DATABASE_URL}/{path}.json?auth={FIREBASE_API_KEY}"
    return fetch_with_backoff(full_url, log_context="Firebase Read")

def update_firebase_quiz(bill_title_slug: str, quiz_data: list, bill_id: str) -> bool:
    """Updates the quiz field in the Firebase Realtime Database."""
    full_url = f"{FIREBASE_DATABASE_URL}/{QUIZ_ROOT_PATH}/{bill_title_slug}.json?auth={FIREBASE_API_KEY}"
    
    # Store the list of questions under a 'questions' key
    payload = {"questions": quiz_data}
    
    response = fetch_with_backoff(full_url, method='PATCH', data=payload, log_context=f"Firebase Write: {bill_id}")
    return response is not None and response.status_code == 200

# --- Core LLM Generation Logic (Using Cerebras SDK) ---

def generate_quiz_from_summary_llm(bill_id: str, bill_title: str, summary: str) -> Union[list[dict], None]:
    """
    Generates a 3-question MCQ quiz using the Cerebras SDK with structured JSON output.
    """
    log_context = f"LLM Gen: {bill_id}"
    
    if not CEREBRAS_CLIENT:
        logging.error(f"[{log_context}] Skipping: Cerebras client is not initialized.")
        return None
        
    logging.info(f"[{log_context}] Preparing Cerebras SDK request for precise quiz generation with model {CEREBRAL_MODEL}...")
    
    # 1. Define the Strict JSON Schema Description for reliable output
    quiz_schema = {
        "type": "ARRAY",
        "minItems": 3,
        "maxItems": 3,
        "items": {
            "type": "OBJECT",
            "required": ["question", "correct_answer", "options"],
            "properties": {
                "question": {"type": "STRING", "description": "The multiple-choice question."},
                "correct_answer": {"type": "STRING", "description": "The single, factually correct answer."},
                "options": {
                    "type": "ARRAY",
                    "minItems": 4,
                    "maxItems": 4,
                    "items": {"type": "STRING"},
                    "description": "An array of exactly four unique strings: one correct answer and three plausible, unique distractors, shuffled randomly."
                }
            },
            "propertyOrdering": ["question", "correct_answer", "options"]
        }
    }
    
    # 2. Define the System Instruction (Persona & Strict Rules)
    system_prompt = (
        "You are an expert legislative analyst and quiz generator. Your task is to generate a highly specific, "
        "3-question multiple-choice quiz based ONLY on the provided bill summary. "
        "The output MUST strictly adhere to the required JSON format which is an array of 3 quiz objects. "
        "For each question, the four options MUST be unique, plausible, and include one correct answer and three unique, incorrect distractors. "
        "The correct answer MUST be included in the 'options' array. DO NOT include any explanatory text outside of the JSON block."
    )
    
    # 3. Define the User Prompt (Task & Source Material)
    user_query = (
        f"Generate a 3-question multiple-choice quiz based on the following Bill Summary. "
        f"The title of the bill is: '{bill_title}'.\n\n"
        f"SUMMARY:\n---\n{summary}\n---\n\n"
        f"Ensure the output conforms exactly to the JSON schema: {json.dumps(quiz_schema)}"
    )

    try:
        # 4. Execute the API Call using the Cerebras SDK
        # The SDK handles authentication, retries, and request formatting
        completion = CEREBRAS_CLIENT.chat.completions.create(
            model=CEREBRAL_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            # Enforce JSON object output format for reliable parsing
            response_format={"type": "json_object"}, 
            temperature=0.0 # Set to 0 for maximum factual adherence and strict formatting
        )
        
        # 5. Extract and parse the generated JSON string
        json_text = completion.choices[0].message.content
        quiz_data = json.loads(json_text)
            
        if isinstance(quiz_data, list) and len(quiz_data) == 3:
            logging.info(f"[{log_context}] Successfully generated and parsed a 3-question quiz.")
            
            # Final validation check
            validated_quiz = []
            for i, q in enumerate(quiz_data):
                if q['correct_answer'] in q['options']:
                    validated_quiz.append(q)
                else:
                    logging.warning(f"[{log_context}] Validation Failure Q{i+1}: Correct answer not found in options array. Skipping question.")
            
            return validated_quiz if len(validated_quiz) == 3 else None

        else:
            logging.error(f"[{log_context}] LLM output structure failed final validation. Expected 3 items, received {len(quiz_data) if isinstance(quiz_data, list) else 'non-list'}. Raw JSON: {json_text[:200]}...")
            return None
                
    except (json.JSONDecodeError, KeyError, IndexError, TypeError) as e:
        # Log the failure type and the content that failed
        error_content = json_text[:500] if 'json_text' in locals() else "Unknown response"
        logging.error(f"[{log_context}] FATAL Parsing Error: {type(e).__name__} - {e}. Raw response start: {error_content}...")
        return None
    except Exception as e:
        # Catch network errors or SDK exceptions
        logging.error(f"[{log_context}] Cerebras SDK API Call Failed: {type(e).__name__} - {e}")
        return None


# --- Main Execution Loop ---

def loop_through_summaries():
    """Main function to coordinate fetching summaries, generating quizzes, and updating."""
    logging.info('--- Starting CEREBRAS SDK-based quiz generation process with Llama model ---')
    
    # Get initial data
    response = get_firebase_data(DATABASE_ROOT_PATH)
    if response is None:
        logging.error(f"Failed to fetch bill data from Firebase.")
        return
        
    bills_data = response.json()

    if not bills_data:
        logging.warning(f"No bill data found at the database path: {DATABASE_ROOT_PATH}")
        return

    bill_items = list(bills_data.items())
    total_bills = len(bill_items)
    
    for index, (bill_id, bill_data) in enumerate(bill_items):
        processed_count = index + 1
        
        summary = bill_data.get('summary')
        title = bill_data.get('title')
        
        # Log the specific bill being processed
        logging.info(f"\n[BEGIN {processed_count}/{total_bills}] Bill ID: {bill_id} | Title: {title or 'N/A'}")
        
        if not summary or not title:
            missing = 'summary' if not summary else ('title' if not title else '')
            logging.warning(f"[{bill_id}] --> Skipping: Missing {missing} data field.")
            continue
            
        # Create the slug for the Firebase key
        try:
            bill_title_slug = slugify(title)
        except Exception:
            bill_title_slug = bill_id
            logging.warning(f"[{bill_id}] --> Failed to generate title slug, using bill ID as slug: {bill_title_slug}")
        
        # 1. Generate Quiz using the robust LLM function
        quiz_data = generate_quiz_from_summary_llm(bill_id, title, summary) 
            
        if quiz_data:
            # 2. Save/Overwrite Quiz
            if update_firebase_quiz(bill_title_slug, quiz_data, bill_id): 
                logging.info(f"[{bill_id}] --> Successfully saved/overwrote quiz to Firebase at {QUIZ_ROOT_PATH}/{bill_title_slug}.")
            else:
                # Log detailed failure to save
                logging.error(f"[{bill_id}] --> FAILED to save quiz data to Firebase for slug: {bill_title_slug}.")
        else:
            # Log detailed failure to generate
            logging.error(f"[{bill_id}] --> FAILED to generate a valid 3-question quiz after Cerebras processing.")

    logging.info('\n--- ALL SUMMARIES PROCESSED SUCCESSFULLY ---')

if __name__ == '__main__':
    # Add a check to ensure the client initialized before starting the main loop
    if CEREBRAS_CLIENT:
        loop_through_summaries()
    else:
        logging.critical("Cannot run loop: Cerebras Client failed initialization. Check API key and network.")
