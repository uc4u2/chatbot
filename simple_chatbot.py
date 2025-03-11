from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
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

# Function to load knowledge dynamically for each website
def load_knowledge(site):
    knowledge_file = f"knowledge_{site}.txt"

    if os.path.exists(knowledge_file):
        with open(knowledge_file, "r", encoding="utf-8") as f:
            return f.read()
    else:
        return f"No custom knowledge available for {site}. Ask me general questions!"

# Function to Serve Chatbot UI (HTML)
def get_html_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            background-color: #f4f4f4;
            margin: 0;
        }
        .chat-container {
            width: 90%;
            max-width: 400px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        }
        h2 {
            text-align: center;
            margin-bottom: 10px;
        }
        textarea {
            width: 100%;
            height: 250px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            resize: none;
            overflow-y: auto;
        }
        input {
            width: 75%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-top: 10px;
        }
        button {
            width: 20%;
            padding: 10px;
            border: none;
            background-color: #28a745;
            color: white;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover {
            background-color: #218838;
        }
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

                const site = window.location.hostname;  // Detect the domain dynamically

                fetch(`/chat/${site}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: message })
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

@app.get("/", response_class=HTMLResponse)
def serve_html():
    return get_html_page()

@app.post("/chat/{site}")
def chat(site: str, request: ChatRequest):
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Load knowledge based on the site making the request
    custom_knowledge = load_knowledge(site)

    try:
        system_prompt = f"""
        You are a chatbot for the website '{site}'.
        - Use the knowledge base specific to this site.
        - If the knowledge base does not cover the topic, provide general helpful responses.
        - Keep the conversation engaging and user-friendly.
        {custom_knowledge}
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
        return {"reply": f"Sorry, I'm having trouble right now. {str(e)}"}
