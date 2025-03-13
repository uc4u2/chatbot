from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import openai
import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY in your .env file.")

# Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Enable CORS (for frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL if necessary
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Files (CSS, JS, PDF)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str

# Load custom knowledge from knowledge.txt
knowledge_file = "knowledge.txt"

if os.path.exists(knowledge_file):
    with open(knowledge_file, "r", encoding="utf-8") as f:
        custom_knowledge = f.read()
else:
    custom_knowledge = "No custom knowledge available."

@app.get("/", response_class=HTMLResponse)
def serve_html():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        return HTMLResponse(content=file.read())

@app.get("/resume")
async def serve_resume():
    resume_path = "static/Yousef_Jalali_Resume.pdf"
    if os.path.exists(resume_path):
        return FileResponse(resume_path, filename="Yousef_Jalali_Resume.pdf")
    else:
        raise HTTPException(status_code=404, detail="Resume file not found.")

@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # Load knowledge based on the site making the request
        system_prompt = f"""
        You are a highly intelligent and logical chatbot.
        Your primary role is to assist users based on the knowledge base provided below.

        KNOWLEDGE BASE:
        {custom_knowledge}

        INSTRUCTIONS:
        - If the user's question can be answered **using logic and inference**, provide the best possible answer.
        - If you have relevant information **but it requires reasoning**, **attempt to deduce the answer**.
        - If the knowledge base **does not** cover the topic, politely inform the user, but try to provide **a general educated guess** if applicable.
        - Keep responses **engaging, helpful, and conversational**.

        EXAMPLES:
        ❌ Bad: "I'm sorry, I can't calculate."
        ✅ Good: "Based on the provided information, Yousef started university at 18 in 2000, meaning he would be around 42-43 years old today."

        Let's begin! Answer the user's queries effectively and intelligently.
        """

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
