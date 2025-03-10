from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import openai
import os
import os
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY in your .env file.")

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

# Function to Serve HTML
def get_html_page():
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Chatbot</title>
</head>
<body>
    <h2>Chat with AI</h2>
    <textarea id="chat" rows="10" cols="50" readonly></textarea><br>
    <input type="text" id="message" placeholder="Type your message...">
    <button id="sendButton">Send</button>

    <script>
        document.addEventListener("DOMContentLoaded", function() {
            document.getElementById("sendButton").addEventListener("click", sendMessage);
            document.getElementById("message").addEventListener("keypress", function(event) {
                if (event.key === "Enter") {
                    sendMessage();
                }
            });
        });

        function sendMessage() {
            const message = document.getElementById("message").value.trim();
            if (!message) return;

            const chatBox = document.getElementById("chat");
            chatBox.value += "You: " + message + "\\n";
            document.getElementById("message").value = "";

            fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                chatBox.value += "Bot: " + data.reply + "\\n";
            })
            .catch(error => {
                chatBox.value += "Error: Could not fetch response.\\n";
                console.error("Fetch error:", error);
            });
        }
    </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def serve_html():
    return get_html_page()

@app.post("/chat")
def chat(request: ChatRequest):
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    try:
        # Ensure OpenAI client is properly created
        client = openai.OpenAI(api_key=OPENAI_API_KEY)

        # Provide the chatbot with knowledge
        system_prompt = f"""
        You are a helpful AI assistant. Use the following knowledge to answer the user's question:
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
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {str(e)}")