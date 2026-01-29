import os
import json
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Your API Key integration
API_KEY = 'AIzaSyBHafGzQLmGXIwAXuEuyANNpbe-KXJ_YsM'
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-3-flash-preview')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/review', methods=['POST'])
def review_code():
    try:
        data = request.get_json()
        user_code = data.get('code', '')
        language = data.get('language', 'Auto-detect')

        # Separate work instructions bound to the JSON structure
        prompt = f"""
        Act as a Senior Auditor for {language}. Audit the following code:
        ---
        {user_code}
        ---
        Perform these 3 tasks and return ONLY a JSON object:
        1. Fix bugs/syntax for {language} specifically.
        2. Analyze Big-O and execution efficiency.
        3. Audit for security (SQLi, XSS, etc.).

        Output format:
        {{
          "optimized_code": "The full corrected and clean code",
          "quality_score": 85,
          "errors": ["list of syntax/logic bugs"],
          "inefficiencies": ["list of performance issues"],
          "security": ["list of vulnerabilities"]
        }}
        """

        response = model.generate_content(prompt)
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        return jsonify(json.loads(raw_text))

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)