from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import openai
import os
import httpx  # To fetch knowledge from website
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
    site: str  # The website making the request

async def fetch_knowledge(site):
    """ Fetch the knowledge.txt file from the client's website """
    knowledge_url = f"https://{site}/knowledge.txt"

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(knowledge_url, timeout=5)
            response.raise_for_status()
            return response.text.strip()
        except httpx.HTTPStatusError:
            return None  # If the file does not exist
        except httpx.RequestError:
            return None  # If there are network issues

@app.post("/chat")
async def chat(request: ChatRequest):
    site = request.site.strip()
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Fetch knowledge file from the website
    custom_knowledge = await fetch_knowledge(site)

    if custom_knowledge:
        system_prompt = f"""
        You are a chatbot for '{site}'.
        Your primary role is to assist users based on the following knowledge:

        KNOWLEDGE BASE:
        {custom_knowledge}

        INSTRUCTIONS:
        - If the user's question can be answered **using logic and inference**, provide the best possible answer.
        - If the knowledge base **does not** cover the topic, politely inform the user.
        - Keep responses **engaging, helpful, and professional**.
        """
    else:
        system_prompt = f"""
        You are a general AI assistant for '{site}'.
        No specific knowledge file was found for this site, so provide general AI responses.
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
        return {"reply": bot_reply}

    except openai.OpenAIError as e:
        return JSONResponse(status_code=500, content={"reply": f"Error: {str(e)}"})

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

                fetch("https://chatbot-qqjj.onrender.com/chat", {  // Fixed Endpoint
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: message, site: site })  // Send site explicitly
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
