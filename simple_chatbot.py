from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import openai
import os
import requests
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY in your .env file.")

# ✅ Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# ✅ Fix CORS Issues
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔥 Allow all origins for testing (Restrict in production)
    allow_credentials=True,
    allow_methods=["POST"],  # ✅ Ensure POST is allowed
    allow_headers=["*"],  # ✅ Allow custom headers
)

# ✅ Function to load knowledge from S3 based on site
def load_knowledge_from_s3(site):
    s3_url = f"https://chatbot-knowledge-bucket.s3.us-west-1.amazonaws.com/knowledge_{site}.txt"

    try:
        response = requests.get(s3_url)
        if response.status_code == 200:
            return response.text
        else:
            return None  # Return None if file not found
    except requests.RequestException as e:
        print(f"Error fetching knowledge from S3: {e}")
        return None

# ✅ Chatbot API Endpoint (POST Requests Only)
@app.post("/chat")
async def chat(request: Request):
    headers = request.headers

    # ✅ Read Site Name from Headers (Fix CORS Issue)
    site = headers.get("X-Website-Name")
    if not site:
        raise HTTPException(status_code=400, detail="Missing 'X-Website-Name' header.")

    body = await request.json()
    user_message = body.get("message", "").strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # ✅ Load knowledge dynamically from S3
    custom_knowledge = load_knowledge_from_s3(site)

    if custom_knowledge:
        system_prompt = f"""
        You are a chatbot for '{site}'.
        Your job is to assist users based on the knowledge base provided below.

        KNOWLEDGE BASE:
        {custom_knowledge}

        INSTRUCTIONS:
        - If the user's question can be answered **using logic and inference**, provide the best possible answer.
        - If the knowledge base **does not** cover the topic, politely inform the user.
        """
    else:
        system_prompt = f"""
        You are a chatbot for '{site}'.
        No specific knowledge is available, so provide general AI responses.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_message}],
            max_tokens=150
        )

        bot_reply = response.choices[0].message.content.strip()
        return JSONResponse(content={"reply": bot_reply})

    except openai.OpenAIError as e:
        return JSONResponse(status_code=500, content={"reply": f"Error: {str(e)}"})
