import os
import json
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ==========================================
# 1. API CONFIGURATION
# ==========================================
# Hardcoded API key and model as requested
API_KEY = 'AIzaSyCdelupTJTAV9BVNfcQrA3gHF3_9Xd5w1w'
genai.configure(api_key=API_KEY)

# Targeted model: gemini-3-flash-preview
model = genai.GenerativeModel('gemini-3-flash-preview')

@app.route('/')
def index():
    """Renders the main CodeSage dashboard."""
    return render_template('index.html')

@app.route('/review', methods=['POST'])
def review_code():
    """Handles the code review logic by communicating with Gemini."""
    try:
        data = request.get_json()
        user_code = data.get('code', '')

        if not user_code:
            return jsonify({"error": "No code provided"}), 400

        # Structured prompt to ensure JSON response
        prompt = f"""
        Act as an Autonomous Code Reviewer. Audit this code:
        ---
        {user_code}
        ---
        Your response must be ONLY a valid JSON object. 
        Do not use markdown blocks or conversational text.
        
        Required JSON Structure:
        {{
          "optimized_code": "The full corrected and clean code",
          "quality_score": 85,
          "errors": ["list of syntax/logic bugs"],
          "inefficiencies": ["list of performance issues"],
          "security": ["list of vulnerabilities like SQLi, XSS"]
        }}
        """

        # Generate content from Gemini
        response = model.generate_content(prompt)
        
        # Strip potential markdown backticks to prevent parsing errors
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        
        # Convert raw text to JSON and send back to frontend
        result = json.loads(raw_text)
        return jsonify(result)

    except json.JSONDecodeError:
        print("AI Output was not valid JSON.")
        return jsonify({"error": "AI response format error. Try again."}), 500
    except Exception as e:
        print(f"Backend Server Error: {str(e)}")
        return jsonify({"error": "Connection to Gemini failed. Check API key status."}), 500

if __name__ == '__main__':
    app.run(debug=True)