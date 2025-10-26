# --- PYTHON PREREQUISITES ---
# This script requires the following packages installed:
# pip install requests torch transformers
# -----------------------------

import requests
import time
import json
import logging
import torch # Import PyTorch to check for GPU availability
from transformers import pipeline

# Configure basic logging for visibility
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# --- Configuration ---
# Your provided Firebase configuration details (used for the REST API)
FIREBASE_DATABASE_URL = "https://orwell-ea558-default-rtdb.firebaseio.com"
FIREBASE_API_KEY = "AIzaSyCS07UgX2GnmuufEQET-RYOtm8i0XaZkWk"

# Your provided API Key for Congress.gov (used in the URL)
CONGRESS_API_KEY = "FacEHXl6iKxBi2ejlZV3YtTo9EIPYMoscmDYvTgj" 

# Firebase Database Path
DATABASE_ROOT_PATH = 'congress/bills'

# --- Chunking Constants (Safeguards against 16384 token limit) ---
# Set a conservative character limit (approx. 100,000 characters is ~16,384 tokens)
MAX_INPUT_CHARS = 60000 
# Overlap ensures context is maintained across split chunks
CHUNK_OVERLAP_CHARS = 2000 


# --- Local AI Model Initialization ---
# Check for GPU (NVIDIA CUDA) and select the appropriate device
DEVICE = 0 if torch.cuda.is_available() else -1
if DEVICE == 0:
    logging.info("GPU (CUDA) detected and will be used for acceleration.")
else:
    logging.warning("No GPU detected. Model will run on CPU, which may be slow.")

# Model: nsi319/legal-led-base-16384
# Architecture: Longformer Encoder Decoder (LED) - handles up to 16384 tokens
try:
    logging.info("Initializing local summarization model (nsi319/legal-led-base-16384)...")
    SUMMARIZATION_PIPE = pipeline(
        "summarization", 
        model="nsi319/legal-led-base-16384", 
        # --- ADDED: Use GPU (device=0) if available, otherwise use CPU (device=-1) ---
        device=DEVICE, 
        # The LED architecture handles the long INPUT context automatically.
        # These parameters now control the OUTPUT summary length.
        max_length=250,  # <-- Adjusted to 250 tokens for shorter summaries
        min_length=100,  # <-- Adjusted min length to be proportional to new max length
        # --- NEW PARAMETERS FOR GENERATION QUALITY AND REPETITION ---
        num_beams=8,              # INCREASED to 8 for higher quality, more complete summaries
        no_repeat_ngram_size=4,   # INCREASED to 4 to aggressively prevent repetition
        length_penalty=2.0,       # NEW: Encourages the model to generate a longer output
        do_sample=False
    )
    logging.info("Model initialization complete.")
except Exception as e:
    logging.error(f"Failed to initialize local AI model. Ensure 'requests', 'torch', and 'transformers' are installed. Error: {e}")
    SUMMARIZATION_PIPE = None

# --- Utility Functions ---

def add_api_key_to_url(url: str, api_key: str) -> str:
    """Safely appends the API key to a URL, using ? or & as appropriate."""
    if '?' in url:
        return f"{url}&api_key={api_key}"
    else:
        return f"{url}?api_key={api_key}"

def fetch_with_backoff(url: str, retries: int = 5, delay: int = 1) -> requests.Response | None:
    """Robust fetch using requests with exponential backoff."""
    for i in range(retries):
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code == 429 and i < retries - 1:
                logging.warning(f"Rate limit hit. Retrying in {delay * (2 ** i)}s...")
                time.sleep(delay * (2 ** i))
                continue
            
            response.raise_for_status() # Raise an exception for HTTP error codes (4xx or 5xx)
            return response
            
        except requests.exceptions.RequestException as error:
            if i == retries - 1:
                logging.error(f"HTTP Error fetching {url} after {retries} retries: {error}")
                return None
            time.sleep(delay * (2 ** i))
    return None

def fetch_raw_text(url: str) -> str | None:
    """Fetches raw text content from a URL (used for XML)."""
    try:
        response = fetch_with_backoff(url)
        if response:
            return response.text
        return None
    except Exception as e:
        logging.error(f"Error fetching raw text from {url}: {e}")
        return None

def get_firebase_data(path: str) -> dict | None:
    """Fetches data from the Firebase Realtime Database REST API."""
    full_url = f"{FIREBASE_DATABASE_URL}/{path}.json?auth={FIREBASE_API_KEY}"
    response = fetch_with_backoff(full_url)
    if response and response.status_code == 200:
        return response.json()
    return None

def update_firebase_summary(bill_id: str, summary: str):
    """Updates the summary field in the Firebase Realtime Database via REST API (PATCH)."""
    full_url = f"{FIREBASE_DATABASE_URL}/{DATABASE_ROOT_PATH}/{bill_id}.json?auth={FIREBASE_API_KEY}"
    payload = {"summary": summary}
    
    try:
        response = requests.patch(full_url, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to update Firebase for {bill_id}: {e}")
        return False

# --- Core Logic Functions ---

def fetch_bill_text(bill_data: dict) -> str | None:
    """
    Executes the explicit, multi-step API chain to find the final XML bill text.
    """
    initial_api_url = bill_data.get('url')
    
    if not initial_api_url:
        logging.error("  --> Error: Could not find the initial congress.gov API URL in the bill data.")
        return None

    try:
        # --- Step 1: Fetch initial Bill URL (The link from Firebase) ---
        step1_url = add_api_key_to_url(initial_api_url, CONGRESS_API_KEY)
        logging.info("  --> Fetching intermediate link 1 (Bill Details): %s", step1_url)
        
        response1 = fetch_with_backoff(step1_url)
        if not response1: return None
        data1 = response1.json()
        
        # Navigate into the 'bill' object
        bill_content = data1.get('bill')
        if not bill_content:
            logging.error("  --> Error: Top-level 'bill' object not found in first response.")
            return None

        # Target: billContent -> textVersions (object) -> url 
        text_versions_object = bill_content.get('textVersions')
        if not text_versions_object or not text_versions_object.get('url'):
            logging.error("  --> Error: 'textVersions' object or its URL not found (likely no text available).")
            return None
        text_versions_api_url = text_versions_object['url']

        # --- Step 2: Fetch the Text Versions URL (The URL found in Step 1) ---
        step2_url = add_api_key_to_url(text_versions_api_url, CONGRESS_API_KEY)
        logging.info("  --> Fetching intermediate link 2 (Text Versions Array): %s", step2_url)

        response2 = fetch_with_backoff(step2_url)
        if not response2: return None
        data2 = response2.json()
        
        # Target: data2 -> textVersions (array)
        text_versions_array = data2.get('textVersions')
        if not isinstance(text_versions_array, list):
            logging.error("  --> Error: 'textVersions' array not found in second response.")
            return None

        # --- Step 3: Find the 'Formatted XML' link in the array ---
        xml_link = None
        for version in text_versions_array:
            formats = version.get('formats', [])
            for f in formats:
                # We specifically look for "Formatted XML" for the full text
                if f.get('type') == "Formatted XML" and f.get('url'):
                    xml_link = f['url']
                    break
            if xml_link:
                break
        
        if not xml_link:
            logging.error("  --> Error: 'Formatted XML' link not found in the final textVersions array.")
            return None

        # --- Step 4: Final XML Fetch ---
        logging.info("  --> Final XML link found. Fetching raw text: %s", xml_link)
        return fetch_raw_text(xml_link)

    except Exception as e:
        logging.error("  --> Fetching Bill Text failed during chained API calls: %s", e)
        return None

def summarize_text_local(bill_text: str) -> str | None:
    """
    Uses the local Legal Longformer (LED) transformer pipeline for summarization.
    Handles chunking and 'Summary of Summaries' for very long bills.
    """
    if SUMMARIZATION_PIPE is None:
        return "Summarization model failed to initialize."
        
    # Final, demanding prompt for the synthesis step
    FINAL_PROMPT = "Generate a complete, well-structured paragraph summarizing this U.S. Congressional bill. Ensure the summary uses proper grammar and complete sentences throughout. The paragraph must finish by providing a conclusive overview of the bill's main ideas and impact, written in clear, simple language suitable for a high school student:"
    
    # Simple XML cleanup to reduce boilerplate noise for the summarizer
    clean_text = bill_text.replace('<?xml version="1.0"?>', '').strip()
    
    # --- CHUNKING LOGIC ---
    if len(clean_text) > MAX_INPUT_CHARS:
        logging.warning(f"  --> Bill text is extremely long ({len(clean_text)} chars). Chunking for processing.")
        
        chunks = []
        start = 0
        while start < len(clean_text):
            end = min(start + MAX_INPUT_CHARS, len(clean_text))
            chunk = clean_text[start:end]
            chunks.append(chunk)
            
            # Move start position back by overlap size for the next chunk
            if end < len(clean_text):
                start += MAX_INPUT_CHARS - CHUNK_OVERLAP_CHARS
            else:
                start = len(clean_text)

        partial_summaries = []
        # 1. Summarize each chunk
        for i, chunk in enumerate(chunks):
            logging.info(f"  --> Summarizing Chunk {i+1}/{len(chunks)}...")
            # Use a simpler prompt for partial summaries
            partial_prompt = "Summarize the key information in this section of the bill:"
            
            try:
                result = SUMMARIZATION_PIPE(f"{partial_prompt} {chunk}")
                if result and result[0].get('summary_text'):
                    partial_summaries.append(result[0]['summary_text'])
            except Exception as e:
                logging.error(f"Failed to summarize chunk {i+1}: {e}")
                
        # 2. Final Summary (Summary of Summaries)
        if not partial_summaries:
            return "Failed to generate any partial summaries due to errors."
            
        concatenated_summaries = " ".join(partial_summaries)
        logging.info("  --> Generating final summary (Summary of Summaries)...")
        
        try:
            # Run the final summarizer on the concatenated summaries
            final_result = SUMMARIZATION_PIPE(f"{FINAL_PROMPT} {concatenated_summaries}")
            if final_result and final_result[0].get('summary_text'):
                return final_result[0]['summary_text']
            else:
                logging.error("AI Response Error: Final summary text not found.")
                return None
        except Exception as e:
            logging.error(f"Failed to call local Summarization Model for final summary: {e}")
            return None

    # --- ORIGINAL LOGIC (for bills within the size limit) ---
    else:
        try:
            result = SUMMARIZATION_PIPE(f"{FINAL_PROMPT} {clean_text}")
            if result and result[0].get('summary_text'):
                return result[0]['summary_text']
            else:
                logging.error("AI Response Error: Summary text not found in pipeline output.")
                return None
        except Exception as error:
            logging.error(f"Failed to call local Summarization Model: {error}")
            return None

# --- Main Execution Loop ---

def loop_through_bills():
    """Main function to coordinate fetching, looping, summarizing, and updating."""
    logging.info('Starting bill summarization process...')

    # 1. Fetch all bills from the specified path
    bills_data = get_firebase_data(DATABASE_ROOT_PATH)

    if not bills_data:
        logging.warning(f"No data found at the database path: {DATABASE_ROOT_PATH}")
        return

    # 2. Convert dictionary keys/values into a list of tuples for ordered iteration
    bill_items = list(bills_data.items())
    total_bills = len(bill_items)
    
    for index, (bill_id, bill_data) in enumerate(bill_items):
        processed_count = index + 1
        logging.info(f"\n[{processed_count}/{total_bills}] Processing Bill ID: {bill_id}")

        # NOTE: This check remains removed to ensure summaries are always overwritten.
        
        # 3. Find and Fetch Bill Text
        bill_text = fetch_bill_text(bill_data)
        
        if not bill_text:
            logging.error(f"  --> Could not find or fetch full bill text for {bill_id}.")
            continue
        # The LED model will handle this large size
        logging.info(f"  --> Fetched bill text successfully ({len(bill_text)} characters).")

        # 4. Generate Summary using local legal LED model
        logging.info("  --> Generating summary with Legal LED (local model)...")
        summary = summarize_text_local(bill_text)
        
        if summary:
            # 5. Update the Database
            # The update_firebase_summary function uses a PATCH request, which overwrites the 'summary' field.
            if update_firebase_summary(bill_id, summary):
                logging.info(f"  --> Successfully saved new summary to Firebase for {bill_id}.")
            else:
                logging.error(f"  --> Failed to save summary to Firebase for {bill_id}.")
        else:
            logging.error(f"  --> Failed to generate summary for {bill_id}.")

    logging.info('\n--- ALL BILLS PROCESSED SUCCESSFULLY ---')

# --- Script Entry Point ---
if __name__ == "__main__":
    # Start the summarization process
    loop_through_bills()
