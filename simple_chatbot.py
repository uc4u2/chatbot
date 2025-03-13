from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import openai
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("Missing OpenAI API key. Set OPENAI_API_KEY in your .env file.")

# Initialize OpenAI Client
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Initialize FastAPI app
app = FastAPI()

# Enable CORS (Required for frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL if necessary
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatRequest(BaseModel):
    message: str
    site: str  # Explicitly send site name from the frontend

# Function to dynamically load knowledge for a site
def load_knowledge(site):
    knowledge_file = f"knowledge_{site}.txt"
    
    if os.path.exists(knowledge_file):
        with open(knowledge_file, "r", encoding="utf-8") as f:
            return f.read()
    return None  # Return None if no knowledge exists

# ✅ **Chatbot API**
@app.post("/chat")
def chat(request: ChatRequest):
    site = request.site.strip().lower()  # Normalize site name
    user_message = request.message.strip()

    if not user_message:
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Load custom knowledge
    custom_knowledge = load_knowledge(site)

    # Construct system prompt
    if custom_knowledge:
        system_prompt = f"""
        You are a highly intelligent and logical chatbot for the website '{site}'.
        Your primary role is to assist users based on the knowledge base provided below.

        KNOWLEDGE BASE:
        {custom_knowledge}

        INSTRUCTIONS:
        - Use **logical reasoning and inference** to provide the best possible answer.
        - If the knowledge base **does not** cover the topic, politely inform the user, but try to **provide an educated guess**.
        - Maintain a **helpful and conversational tone**.
        - **Do not mix knowledge between websites**.

        Example of a smart response:
        ❌ Bad: "I'm sorry, I can't calculate."
        ✅ Good: "Based on the provided information, Yousef started university at 18 in 2000, meaning he would be around 42-43 years old today."

        Now, respond effectively to the user's queries.
        """
    else:
        system_prompt = f"""
        You are an AI chatbot for '{site}'.
        No specific knowledge is available for this site, so provide **accurate and general AI responses**.
        """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=200  # Allow longer responses
        )

        bot_reply = response.choices[0].message.content.strip()

        logger.info(f"Chat Response for {site}: {bot_reply}")
        return {"reply": bot_reply}

    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error: {str(e)}")
        return JSONResponse(status_code=500, content={"reply": "Apologies, I encountered an issue. Please try again."})

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yousef Jalali - AI & Cloud Architect</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
        }
        h1, h2 {
            text-align: center;
        }
        .resume-section {
            margin-bottom: 20px;
        }
        .chat-container {
            margin-top: 20px;
            padding: 20px;
            background: #f9f9f9;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.1);
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
        input, button {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
        }
        button {
            background-color: #28a745;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #218838;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Yousef Jalali</h1>
        <h2>AI & Cloud Solutions Architect</h2>
        <p><strong>Email:</strong> yousefsamak@yahoo.com | <strong>Phone:</strong> +1 (514)-430-0970</p>
        <p><strong>LinkedIn:</strong> <a href="#">LinkedIn Profile</a> | <strong>GitHub:</strong> <a href="#">GitHub Profile</a></p>
        <hr>
        
        <div class="resume-section">
            <h3>Professional Summary</h3>
            <p>AWS Solutions Architect with expertise in designing, deploying, and managing scalable cloud infrastructures. Skilled in AWS services (EC2, S3, Lambda, API Gateway) and automation with Python, React, and PowerShell. Passionate about AI-driven solutions and SEO automation.</p>
        </div>
        
        <div class="resume-section">
            <h3>Key Skills</h3>
            <ul>
                <li>AWS Cloud Architecture (VPC, Lambda, EC2, S3, CloudFormation)</li>
                <li>FastAPI, OpenAI API, Python, React.js</li>
                <li>Infrastructure as Code (CloudFormation, Terraform)</li>
                <li>SEO Automation & Web Performance Optimization</li>
                <li>Serverless & Microservices Architecture</li>
            </ul>
        </div>
        
        <div class="resume-section">
            <h3>Notable Projects</h3>
            <ul>
                <li><strong>Multi-Site AI Chatbot:</strong> Built an AI-driven chatbot using FastAPI & OpenAI, deployable across multiple websites.</li>
                <li><strong>GrandpaOliver.com:</strong> Scalable cloud-native platform for children’s storytelling (AWS Amplify, Stripe, Firebase).</li>
                <li><strong>SEO Automation Platform:</strong> Python-based tool for competitor analysis & search ranking improvements.</li>
            </ul>
        </div>
        
        <div class="resume-section">
            <h3>Download Resume</h3>
            <a href="Yousef_Jalali_Resume.pdf" download><button>Download PDF</button></a>
        </div>
    </div>
    
    <div class="chat-container">
        <h2>Ask AI about me!</h2>
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

                chatBox.value += "You: " + message + "\n";
                inputField.value = "";
                chatBox.scrollTop = chatBox.scrollHeight;

                fetch("/chat", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ message: message, site: "yousefjalali.com" })
                })
                .then(response => response.json())
                .then(data => {
                    chatBox.value += "Bot: " + (data.reply || "I didn't catch that.") + "\n";
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
</html>
