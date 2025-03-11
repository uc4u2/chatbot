from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY in your .env file.")

# Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    site: str  # Website making the request

# Function to load knowledge dynamically for each website
def load_knowledge(site):
    knowledge_file = f"knowledge_{site}.txt"

    if os.path.exists(knowledge_file):
        with open(knowledge_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return None  # If no knowledge file exists, return None

# ✅ **Fixed Chat Logic**
@app.post("/chat")
def chat(request: ChatRequest):
    site = request.site.strip()
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Load knowledge for the specific website
    custom_knowledge = load_knowledge(site)

    if custom_knowledge:
        system_prompt = f"""
        You are a chatbot for '{site}'.
        Your job is to assist users based on the following knowledge:
        
        {custom_knowledge}
        
        If the question is outside your knowledge, provide a polite response and general AI help.
        """
    else:
        system_prompt = "You are a general AI assistant. Provide helpful responses."

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150
        )

        bot_reply = response.choices[0].message.content.strip()
        return {"reply": bot_reply}

    except openai.OpenAIError as e:
        return JSONResponse(status_code=500, content={"reply": f"Error: {str(e)}"})
