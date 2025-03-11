from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY in your .env file.")

# ✅ Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# ✅ Create FastAPI instance
app = FastAPI()

class ChatRequest(BaseModel):
    message: str
    site: str  # Website name sent from frontend

# ✅ Function to load knowledge dynamically for each website
def load_knowledge(site):
    knowledge_file = f"knowledge_{site}.txt"

    if os.path.exists(knowledge_file):
        with open(knowledge_file, "r", encoding="utf-8") as f:
            return f.read()
    return None  # If no file exists, return None

# ✅ Serve Chatbot HTML Page (For Testing)
@app.get("/", response_class=HTMLResponse)
def serve_html(site: str = Query(default="unknown")):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot</title>
    <style>
        body {{ font-family: Arial, sans-serif; text-align: center; padding: 20px; }}
        textarea {{ width: 100%; height: 300px; }}
        input, button {{ padding: 10px; margin-top: 10px; }}
    </style>
</head>
<body>
    <h2>Chat with AI</h2>
    <textarea id="chat" readonly></textarea><br>
    <input type="text" id="message" placeholder="Type your message..." autofocus>
    <button onclick="sendMessage()">Send</button>

    <script>
        const chatBox = document.getElementById("chat");
        const inputField = document.getElementById("message");

        function sendMessage() {{
            const message = inputField.value.trim();
            if (!message) return;
            chatBox.value += "You: " + message + "\\n";
            inputField.value = "";

            fetch("/chat", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify({{ message: message, site: "{site}" }})
            }})
            .then(response => response.json())
            .then(data => {{
                chatBox.value += "Bot: " + (data.reply || "I didn't catch that.") + "\\n";
            }})
            .catch(error => {{
                chatBox.value += "Error: Could not fetch response.\\n";
            }});
        }}

        inputField.addEventListener("keypress", function(event) {{
            if (event.key === "Enter") {{
                sendMessage();
                event.preventDefault();
            }}
        }});
    </script>
</body>
</html>
"""

# ✅ API Endpoint for Chatbot
@app.post("/chat")
def chat(request: ChatRequest):
    site = request.site.strip()
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # ✅ Load knowledge base for the given site
    custom_knowledge = load_knowledge(site)

    if custom_knowledge:
        system_prompt = f"""
        You are a highly intelligent and logical chatbot for the website '{site}'.
        Your primary role is to assist users based on the knowledge base provided below.

        KNOWLEDGE BASE:
        {custom_knowledge}

        INSTRUCTIONS:
        - If the user's question can be answered **using logic and inference**, provide the best possible answer.
        - If you have relevant information **but it requires reasoning**, **attempt to deduce the answer**.
        - If the knowledge base **does not** cover the topic, politely inform the user, but try to provide **a general educated guess** if applicable.
        - Keep responses **engaging, helpful, and conversational**.
        - **Do not mix knowledge between websites.** If the user asks about a topic outside this site's scope, **do not reference other sites**.

        Let's begin! Answer the user's queries effectively and intelligently.
        """
    else:
        system_prompt = f"""
        You are a general AI assistant for the website '{site}'.
        There is no specific knowledge base for this site, so provide general AI responses.
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
