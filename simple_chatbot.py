from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import openai
import os
import requests
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
    site: str  # Explicitly send site name from the frontend

# Function to fetch knowledge from a website
def fetch_knowledge_from_website(site):
    knowledge_url = f"https://{site}/knowledge.txt"
    print(f"📡 Fetching knowledge from: {knowledge_url}")

    try:
        response = requests.get(knowledge_url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Successfully fetched knowledge for {site}")
            return response.text
        else:
            print(f"❌ ERROR: Knowledge file not found for {site} (HTTP {response.status_code})")
            return None
    except requests.RequestException as e:
        print(f"❌ ERROR: Failed to fetch knowledge for {site}: {str(e)}")
        return None

# Function to fetch stored knowledge from the chatbot server
def fetch_knowledge_from_server(site):
    knowledge_file = f"knowledge_{site}.txt"
    if os.path.exists(knowledge_file):
        with open(knowledge_file, "r", encoding="utf-8") as f:
            return f.read()
    return None

# ✅ **Chat Endpoint**
@app.post("/chat")
def chat(request: ChatRequest):
    site = request.site.strip()
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Try fetching knowledge from the website first
    custom_knowledge = fetch_knowledge_from_website(site)

    # If website knowledge is not available, use stored knowledge on the chatbot server
    if not custom_knowledge:
        custom_knowledge = fetch_knowledge_from_server(site)

    if custom_knowledge:
        system_prompt = f"""
        You are a chatbot for '{site}'.
        Your job is to assist users based on the following knowledge:

        {custom_knowledge}

        If the knowledge base does not cover the topic, politely inform the user.
        """
    else:
        system_prompt = f"""
        You are a general AI assistant for '{site}'.
        No specific knowledge is available for this site, so provide general AI responses.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
            max_tokens=150,
        )

        bot_reply = response.choices[0].message.content.strip()
        return {"reply": bot_reply}

    except openai.OpenAIError as e:
        return JSONResponse(status_code=500, content={"reply": f"Error: {str(e)}"})


# ✅ **Upload Knowledge Endpoint (For Manual Uploads)**
@app.post("/upload-knowledge")
def upload_knowledge(request: ChatRequest):
    site = request.site.strip()
    knowledge_content = request.message.strip()

    if not site or not knowledge_content:
        raise HTTPException(status_code=400, detail="Site and knowledge content cannot be empty.")

    # Save to a local file
    knowledge_file = f"knowledge_{site}.txt"
    with open(knowledge_file, "w", encoding="utf-8") as f:
        f.write(knowledge_content)

    return {"status": "success", "message": f"Knowledge for {site} uploaded successfully"}


# ✅ **Frontend Chatbot UI**
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
