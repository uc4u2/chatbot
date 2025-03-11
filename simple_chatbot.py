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
    site: str  # Site URL sent from frontend

# Function to load knowledge dynamically based on the requesting website
def load_knowledge(site):
    knowledge_file = f"knowledge_{site}.txt"

    if os.path.exists(knowledge_file):
        print(f"📄 Loading knowledge file: {knowledge_file}")  # Debugging log
        with open(knowledge_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        print(f"❌ No knowledge file found for: {site}")  # Debugging log
        return None  # No knowledge file exists

# ✅ **Fixed Chat Logic**
@app.post("/chat")
def chat(request: ChatRequest):
    site = request.site.strip()
    user_message = request.message.strip()

    print(f"📩 Received request: site={site}, message={user_message}")  # Debugging

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Load knowledge for the specific website
    custom_knowledge = load_knowledge(site)

    if custom_knowledge:
        system_prompt = f"""
        You are a highly intelligent and logical chatbot for the website '{site}'.
        Your primary role is to assist users based on the knowledge base provided below.

        KNOWLEDGE BASE:
        {custom_knowledge}

        INSTRUCTIONS:
        - If the user's question can be answered **using logic and inference**, provide the best possible answer.
        - If you have relevant information **but it requires reasoning**, **attempt to deduce the answer**.
        - If the knowledge base **does not** cover the topic, politely inform the user, but try to provide **a general educated guess** if applicable.
        - Keep responses **engaging, helpful, and conversational**.
        - **Do not mix knowledge between websites.** If the user asks about a topic outside this site's scope, **do not reference other sites.**

        EXAMPLES OF SMART RESPONSES:
        ❌ Bad: "I'm sorry, I can't calculate."
        ✅ Good: "Based on the provided information, Yousef started university at 18 in 2000, meaning he would be around 42-43 years old today."

        Let's begin! Answer the user's queries effectively and intelligently.
        """
    else:
        system_prompt = f"""
        You are a general AI assistant for the website '{site}'.
        However, there is NO specific knowledge available for this site.
        Please provide general AI responses.
        """

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
        print(f"✅ Response: {bot_reply}")  # Debugging
        return {"reply": bot_reply}

    except openai.OpenAIError as e:
        print(f"❌ OpenAI API Error: {str(e)}")  # Debugging
        return JSONResponse(status_code=500, content={"reply": f"Error: {str(e)}"})
