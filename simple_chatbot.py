from fastapi import FastAPI, HTTPException
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

# Initialize OpenAI Client once for better performance
client = openai.OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    site: str  # Explicitly send site name from the frontend

# Function to load the correct knowledge base for each site
def load_knowledge(site):
    knowledge_file = f"knowledge_{site}.txt"
    print(f"📂 Attempting to load: {knowledge_file}")  # ✅ Debugging

    if os.path.exists(knowledge_file):
        with open(knowledge_file, "r", encoding="utf-8") as f:
            content = f.read()
            print(f"✅ Loaded knowledge ({len(content)} characters)")
            return content
    print("❌ No knowledge file found!")
    return None


# Function to get chatbot responses
def get_openai_response(system_prompt, user_message):
    """
    Calls OpenAI API to generate a response.
    """
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        max_tokens=150
    ).choices[0].message.content.strip()

# ✅ **Chat Endpoint (Faster & Smarter Logic)**
@app.post("/chat")
def chat(request: ChatRequest):
    site = request.site.strip()
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Load site-specific knowledge
    custom_knowledge = load_knowledge(site)

    # Ensure the chatbot only uses relevant knowledge
    if custom_knowledge:
        system_prompt = f"""
        You are a chatbot for '{site}'.
        Your job is to answer questions using ONLY the following knowledge base:

        {custom_knowledge}

        If the knowledge base does not contain the answer, politely let the user know.
        DO NOT provide information that is not in the knowledge base.
        """
    else:
        system_prompt = f"""
        You are a chatbot for '{site}'.
        No specific knowledge is available, so provide general AI assistance.
        """

    try:
        bot_reply = get_openai_response(system_prompt, user_message)
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
        body { font-family: Arial, sans-serif; position: relative; }
        .chat-container { position: fixed; bottom: 20px; right: 20px; width: 350px; height: 500px; 
                          background: white; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2); 
                          overflow: hidden; z-index: 1000; }
        .chat-header { background: #28a745; color: white; text-align: center; padding: 10px; }
        .chat-body { height: 400px; overflow-y: auto; padding: 10px; border-bottom: 1px solid #ddd; }
        .chat-footer { display: flex; padding: 10px; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px; background: #28a745; color: white; border: none; cursor: pointer; }
        button:hover { background: #218838; }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">Chat with AI</div>
        <div class="chat-body" id="chat"></div>
        <div class="chat-footer">
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

                chatBox.innerHTML += "<div><b>You:</b> " + message + "</div>";
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
                    chatBox.innerHTML += "<div><b>Bot:</b> " + (data.reply || "I didn't catch that.") + "</div>";
                    chatBox.scrollTop = chatBox.scrollHeight;
                })
                .catch(error => {
                    chatBox.innerHTML += "<div style='color:red;'><b>Error:</b> Could not fetch response.</div>";
                    console.error("Fetch error:", error);
                });
            }
        });
    </script>
</body>
</html>"""
