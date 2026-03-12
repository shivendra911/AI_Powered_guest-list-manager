import os
import json
import requests
import google.generativeai as genai
from flask import current_app

class LLMService:
    def __init__(self):
        self.gemini_model = None
        self.system_prompt = """
        You are an AI assistant for a Guest List Manager application. 
        Your job is to understand user requests and return JSON instructions.
        You can handle guests, events, and RSVPs.
        Always return ONLY valid JSON in format: 
        {"operation": "add|delete|list|search|record", "entity": "guest|event|rsvp", "parameters": {}}
        """

    def _init_gemini(self):
        if not self.gemini_model:
            api_key = current_app.config.get('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash')
        return self.gemini_model is not None

    def interpret_command(self, user_message):
        """Try Gemini first, fallback to Ollama if it fails"""
        try:
            if self._init_gemini():
                chat = self.gemini_model.start_chat()
                response = chat.send_message(f"{self.system_prompt}\nUser request: {user_message}")
                
                # Try to parse json from Gemini response
                text = response.text.strip()
                if text.startswith('```json'): text = text[7:]
                if text.endswith('```'): text = text[:-3]
                
                return json.loads(text.strip())
        except Exception as e:
            current_app.logger.warning(f"Gemini API failed or not configured: {str(e)}. Falling back to Ollama.")
            return self._fallback_ollama(user_message)
            
        return self._fallback_ollama(user_message)

    def _fallback_ollama(self, user_message):
        """Fallback to local Ollama Llama 3.2 model"""
        model_name = current_app.config.get('OLLAMA_MODEL', 'llama3.2')
        api_url = current_app.config.get('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
        
        prompt = f"{self.system_prompt}\nUser request: {user_message}\nReturn ONLY JSON."
        
        try:
            response = requests.post(api_url, json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=30)
            
            if response.status_code == 200:
                return json.loads(response.json()['response'])
            else:
                current_app.logger.error(f"Ollama API returned status {response.status_code}")
                return {"error": "Local AI also failed."}
        except requests.exceptions.RequestException as e:
            current_app.logger.error(f"Failed to connect to Ollama: {str(e)}")
            return {"error": "Could not connect to AI services. Please verify API key or ensure Ollama is running."}

    def generate_chat_response(self, user_message):
        """For conversational messages (hello, advice)"""
        system = "You are a helpful AI event planner. Keep answers friendly and concise."
        
        try:
            if self._init_gemini():
                response = self.gemini_model.generate_content(f"{system}\nUser: {user_message}")
                return response.text
        except Exception:
            pass # Fall back to Ollama
            
        model_name = current_app.config.get('OLLAMA_MODEL', 'llama3.2')
        api_url = current_app.config.get('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
        
        try:
            response = requests.post(api_url, json={
                "model": model_name,
                "prompt": f"{system}\nUser: {user_message}",
                "stream": False
            }, timeout=30)
            if response.status_code == 200:
                return response.json()['response']
        except Exception:
            return "Hi there! I'm currently having trouble connecting to my AI brain. How can I help you manually?"

    def analyze_sentiment(self, text):
        """Analyze sentiment using Gemini, fallback to Ollama"""
        prompt = f"""
        Analyze the sentiment of the following text related to an event or guest feedback:
        
        "{text}"
        
        Provide a sentiment score from -10 (extremely negative) to +10 (extremely positive),
        along with a brief explanation and key sentiment features. Format your response as JSON:
        {{
            "score": [score],
            "sentiment": "[overall sentiment category]",
            "explanation": "[brief explanation]",
            "key_points": ["point1", "point2", ...]
        }}
        """
        
        # Try Gemini
        try:
            if self._init_gemini():
                response = self.gemini_model.generate_content(prompt)
                clean_text = response.text.strip()
                if clean_text.startswith("```json"): clean_text = clean_text[7:]
                if clean_text.endswith("```"): clean_text = clean_text[:-3]
                return json.loads(clean_text.strip())
        except Exception as e:
            current_app.logger.warning(f"Gemini Sentiment failed: {str(e)}. Falling back to Ollama.")
            pass
            
        # Fallback to Ollama
        model_name = current_app.config.get('OLLAMA_MODEL', 'llama3.2')
        api_url = current_app.config.get('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
        
        try:
            response = requests.post(api_url, json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }, timeout=30)
            
            if response.status_code == 200:
                result = response.json()['response'].strip()
                return json.loads(result)
            else:
                return {"error": "Local AI fallback failed with status " + str(response.status_code)}
        except requests.exceptions.RequestException as e:
            return {"error": "Could not connect to local AI. Please verify Ollama is running."}
        except json.JSONDecodeError:
            return {"error": "Local AI returned invalid JSON format."}
