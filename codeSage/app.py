import os
import json
import re
import time
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv # Import this

# Load the keys from the invisible .env file
load_dotenv()

app = Flask(__name__)

# ==========================================
# 1. SECURE KEY LOADING
# ==========================================
# Now the keys are not in your code, so GitHub won't complain!
API_KEYS = [
    os.getenv("GEMINI_KEY_1"),
    os.getenv("GEMINI_KEY_2"),
    os.getenv("GEMINI_KEY_3"),
    os.getenv("GEMINI_KEY_4"),
    os.getenv("GEMINI_KEY_5"),
    os.getenv("GEMINI_KEY_6")
]

# Filter out any None values in case a key is missing
API_KEYS = [key for key in API_KEYS if key]

if not API_KEYS:
    raise ValueError("No API keys found! Make sure you created the .env file.")

class KeyManager:
    def __init__(self, keys):
        self.keys = keys
        self.current_index = 0

    def get_key(self):
        return self.keys[self.current_index]

    def rotate(self):
        self.current_index = (self.current_index + 1) % len(self.keys)
        print(f"🔄 Switching to Key #{self.current_index + 1}")
        return self.get_key()

key_manager = KeyManager(API_KEYS)

# ... (Rest of your code remains exactly the same) ...
# ... Copy the generate_with_failover, extract_json, and routes from the previous code ...

# ==========================================
# 2. FAILOVER LOGIC
# ==========================================
def generate_with_failover(prompt, model_name='gemini-3-flash-preview'):
    """
    Tries to generate content. If it hits a rate limit (429) or overload (503),
    it automatically rotates to the next key and retries instantly.
    """
    max_retries = len(API_KEYS) # Ensure we try every key at least once
    
    for attempt in range(max_retries):
        try:
            # 1. Configure the active key
            current_key = key_manager.get_key()
            genai.configure(api_key=current_key)
            model = genai.GenerativeModel(model_name)

            # 2. Attempt generation
            # print(f"Attempting with Key #{key_manager.current_index + 1}...") 
            response = model.generate_content(prompt)
            
            # If we get a valid object back, return it
            if response and hasattr(response, 'text'):
                return response
            else:
                raise ValueError("Empty response from AI")

        except Exception as e:
            error_msg = str(e)
            print(f"⚠️ Key #{key_manager.current_index + 1} Error: {error_msg}")
            
            # Check for Rate Limits (429) or Service Overload (503)
            if "429" in error_msg or "503" in error_msg:
                key_manager.rotate()
                # No sleep needed here because we are switching to a FRESH key
                continue 
            else:
                # If it's a code error (like 400 Bad Request), stop trying
                raise e
    
    # If all keys fail
    raise Exception("All API keys are currently exhausted or busy.")

# ==========================================
# 3. FLASK ROUTES
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/review', methods=['POST'])
def review_code():
    try:
        # --- INPUT VALIDATION ---
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400
            
        user_code = data.get('code', '')
        language = data.get('language', 'Auto-detect')

        if not user_code.strip():
            return jsonify({"error": "Please enter some code to analyze."}), 400

        # --- SYSTEM PROMPT ---
        prompt = f"""
        Act as a Senior Code Auditor for {language}. 
        Analyze the code below. You must return ONLY valid JSON.
        
        CODE TO REVIEW:
        ---
        {user_code}
        ---

        REQUIRED JSON STRUCTURE (Do not use Markdown blocks):
        {{
          "optimized_code": "The full corrected code string (escape quotes properly)",
          "quality_score": 85,
          "errors": ["list of specific bugs"],
          "inefficiencies": ["list of performance issues"],
          "security": ["list of vulnerabilities"]
        }}
        """

        # --- GENERATION WITH ROTATION ---
        # This function handles the 6-key rotation logic
        response = generate_with_failover(prompt)

        # --- TRIPLE-LAYER CLEANING ---
        raw_text = response.text.strip()
        
        # 1. Remove Markdown Code Blocks (```json ... ```)
        if "```" in raw_text:
            parts = raw_text.split("```")
            for part in parts:
                if "{" in part and "}" in part: # Find the part that looks like JSON
                    raw_text = part
                    if raw_text.startswith("json"):
                        raw_text = raw_text[4:] # Strip 'json' label
                    break
        
        raw_text = raw_text.strip()

        # 2. Safe JSON Parsing
        try:
            final_data = json.loads(raw_text)
            return jsonify(final_data)
        except json.JSONDecodeError as je:
            print(f"JSON Parse Error: {je}")
            print(f"Bad Raw Text: {raw_text}")
            return jsonify({"error": "AI returned invalid format. Please retry."}), 500

    except Exception as e:
        print(f"Critical Server Error: {e}")
        return jsonify({"error": str(e)}), 500
# ... (Previous code) ...

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

# ... (End of file) ...

if __name__ == '__main__':
    app.run(debug=True)