from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import openai
import os
import requests
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ Missing OpenAI API key. Set OPENAI_API_KEY in your .env file.")

# ✅ Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Define FastAPI app
app = FastAPI()

# ✅ Enable CORS (Fixes "Method Not Allowed" error)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains (change to a list of domains for security)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# ✅ S3 Bucket Configuration
S3_BUCKET_URL = "https://chatbot-knowledge-bucket.s3.us-east-1.amazonaws.com"

class ChatRequest(BaseModel):
    message: str
    site: str  # Website making the request

# ✅ Function to fetch knowledge from S3
def fetch_knowledge(site):
    knowledge_file_url = f"{S3_BUCKET_URL}/knowledge_{site}.txt"

    try:
        print(f"📂 Fetching knowledge from: {knowledge_file_url}")  # Debugging
        response = requests.get(knowledge_file_url)

        print(f"📡 Response status: {response.status_code}")  # Debugging
        if response.status_code == 200:
            print(f"✅ Knowledge file found for {site}.")
            return response.text
        else:
            print("❌ Knowledge file not found.")
            return None
    except requests.RequestException as e:
        print(f"❌ Failed to fetch knowledge: {str(e)}")
        return None

# ✅ API Route: Chat Endpoint
@app.post("/chat")
def chat(request: ChatRequest):
    site = request.site.strip()
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # ✅ Load site-specific knowledge
    custom_knowledge = fetch_knowledge(site)

    if custom_knowledge:
        system_prompt = f"""
        You are a highly intelligent chatbot for the website '{site}'.
        Your primary job is to provide helpful and accurate answers using the knowledge base provided.

        KNOWLEDGE BASE:
        {custom_knowledge}

        INSTRUCTIONS:
        - If the knowledge base **contains relevant information**, use it to answer.
        - If the knowledge base **does NOT contain** the answer, acknowledge that and provide a general response.
        - **Do not mix knowledge between websites.**
        """
    else:
        system_prompt = f"""
        You are an AI chatbot for '{site}', but no specific knowledge is available.
        Provide general helpful responses but acknowledge that no custom information is available.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200
        )

        bot_reply = response.choices[0].message.content.strip()
        return {"reply": bot_reply}

    except openai.OpenAIError as e:
        return JSONResponse(status_code=500, content={"reply": f"Error: {str(e)}"})


# ✅ API Route: Embedded Chatbot UI for Testing
@app.get("/", response_class=HTMLResponse)
def serve_html():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f4f4f4; margin: 0; }
        .chat-container { width: 90%; max-width: 400px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); }
        h2 { text-align: center; margin-bottom: 10px; }
        textarea { width: 100%; height: 250px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; resize: none; overflow-y: auto; }
        input { width: 75%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-top: 10px; }
        button { width: 20%; padding: 10px; border: none; background-color: #28a745; color: white; border-radius: 5px; cursor: pointer; }
        button:hover { background-color: #218838; }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>Chat with AI</h2>
        <textarea id="chat" readonly></textarea>
        <div>
            <input type="text" id="message" placeholder="Type your message..." autofocus>
            <button id="sendButton">Send</button>
        </div>
    </div>

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            const chatBox = document.getElementById("chat");
            const inputField = document.getElementById("message");
            const sendButton = document.getElementById("sendButton");

            sendButton.addEventListener("click", sendMessage);
            inputField.addEventListener("keypress", function(event) {
                if (event.key === "Enter") {
                    sendMessage();
                    event.preventDefault();
                }
            });

            function sendMessage() {
                const message = inputField.value.trim();
                if (!message) return;

                chatBox.value += "You: " + message + "\\n";
                inputField.value = "";
                chatBox.scrollTop = chatBox.scrollHeight;

                const site = window.location.hostname;

                fetch("https://chatbot-qqjj.onrender.com/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: message, site: site })
                })
                .then(response => response.json())
                .then(data => {
                    chatBox.value += "Bot: " + (data.reply || "I didn't catch that.") + "\\n";
                    chatBox.scrollTop = chatBox.scrollHeight;
                })
                .catch(error => {
                    chatBox.value += "Error: Could not fetch response.\\n";
                    console.error("Fetch error:", error);
                });
            }
        });
    </script>
</body>
</html>"""
