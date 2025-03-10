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
        knowledge = f.read().split("\n")
    for line in knowledge:
        if user_message.lower() in line.lower():
            return f"I found this in my knowledge base: {line.strip()}"
    return None

# Improved System Prompt
system_prompt = """
You are a friendly, conversational AI assistant. Your goal is to provide natural, engaging responses like a human assistant.
- Always respond in a casual, friendly way.
- Use knowledge from the knowledge base only if it is directly related to the user's question.
- If a user just says "hi" or "hello", greet them normally.
- If the question is not covered by the knowledge base, respond naturally as an AI assistant.
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
                    chatBox.value += "Bot: " + (data.reply || "[No response received]") + "\n";
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

chat_history = []  # Store the last 5 messages for better context

@app.post("/chat")
async def chat(request: ChatRequest):
    user_message = request.message.strip()
    if not user_message:
        return {"reply": "I didn't catch that. Can you say it again?"}
    
    if user_message.lower() in ["hi", "hello", "hey"]:
        return {"reply": "Hey there! How can I help you today?"}
    
    local_response = search_knowledge_base(user_message)
    if local_response:
        return {"reply": local_response}
    
    chat_history.append({"role": "user", "content": user_message})
    if len(chat_history) > 5:
        chat_history.pop(0)
    
    response = await asyncio.to_thread(
        client.chat.completions.create,
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt}
        ] + chat_history,
        max_tokens=150
    )
    
    bot_reply = response.choices[0].message.content.strip() if response.choices else "I'm not sure how to respond to that."
    
    chat_history.append({"role": "assistant", "content": bot_reply})
    if len(chat_history) > 5:
        chat_history.pop(0)
    
    return {"reply": bot_reply}
