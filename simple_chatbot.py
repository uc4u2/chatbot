from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel
import openai
import os
import asyncio
from functools import lru_cache

# Load environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY in Render environment variables.")

# Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

# Load custom knowledge from knowledge.txt
knowledge_file = "knowledge.txt"
if os.path.exists(knowledge_file):
    with open(knowledge_file, "r", encoding="utf-8") as f:
        custom_knowledge = f.read()
else:
    custom_knowledge = "No custom knowledge available."

# Function to Search Local Knowledge
def search_knowledge_base(user_message):
    with open("knowledge.txt", "r", encoding="utf-8") as f:
        knowledge = f.read()
    for line in knowledge.split("\n"):
        if user_message.lower() in line.lower():
            return line.strip()
    return None

# Cache Responses to Reduce API Calls
@lru_cache(maxsize=50)
def get_cached_response(user_message):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=150
    )
    return response.choices[0].message.content.strip()

# Improved System Prompt
system_prompt = f"""
You are a friendly and conversational AI assistant. Your goal is to have natural, engaging conversations while also using the knowledge provided. 
- Keep responses short and to the point.
- If the user says "hi" or "hello", greet them naturally.
- If the user asks a personal question like "do you know Yousef?" only respond if there is relevant knowledge. Otherwise, say you don’t know.
- If the user asks something not in the knowledge base, respond as a general AI assistant.
{custom_knowledge}
"""

# Function to Serve HTML
def get_html_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #f4f4f4; padding: 20px; }
        .chat-container { max-width: 400px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1); }
        textarea { width: 100%; height: 250px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; resize: none; overflow-y: auto; }
        input { width: 75%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { width: 20%; padding: 10px; background-color: #28a745; color: white; border-radius: 5px; cursor: pointer; }
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
                if (event.key === "Enter") { sendMessage(); }
            });
            function sendMessage() {
                const message = inputField.value.trim();
                if (!message) return;
                chatBox.value += "You: " + message + "\n";
                inputField.value = "";
                chatBox.scrollTop = chatBox.scrollHeight;
                fetch("/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: message })
                })
                .then(response => response.json())
                .then(data => {
                    chatBox.value += "Bot: " + data.reply + "\n";
                    chatBox.scrollTop = chatBox.scrollHeight;
                })
                .catch(error => {
                    chatBox.value += "Error: Could not fetch response.\n";
                    console.error("Fetch error:", error);
                });
            }
        });
    </script>
</body>
</html>"""

@app.get("/", response_class=HTMLResponse)
def serve_html():
    return get_html_page()

chat_history = []  # Memory for user conversation

@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message.strip()
    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")
    chat_history.append({"role": "user", "content": user_message})
    if len(chat_history) > 5:
        chat_history.pop(0)
    local_response = search_knowledge_base(user_message)
    if local_response:
        return {"reply": local_response}
    async def fetch_openai_response():
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
            ] + chat_history,
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    bot_reply = await fetch_openai_response()
    chat_history.append({"role": "assistant", "content": bot_reply})
    if len(chat_history) > 5:
        chat_history.pop(0)
    return {"reply": bot_reply}