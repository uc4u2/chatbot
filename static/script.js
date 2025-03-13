document.addEventListener("DOMContentLoaded", function() {
    const chatBox = document.getElementById("chatbox");
    const openChat = document.getElementById("open-chat");
    const closeChat = document.getElementById("close-chat");
    const chatMessages = document.getElementById("chat-messages");
    const inputField = document.getElementById("message");
    const sendButton = document.getElementById("sendButton");

    // Open chatbox by default
    chatBox.style.display = "block";

    // Welcome Message
    addMessage("Bot", "Hello! I'm your AI assistant. Ask me anything about Yousef's experience!");

    openChat.addEventListener("click", function() {
        chatBox.style.display = "block";
    });

    closeChat.addEventListener("click", function() {
        chatBox.style.display = "none";
    });

    sendButton.addEventListener("click", sendMessage);
    inputField.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            event.preventDefault();
            sendMessage();
        }
    });

    function sendMessage() {
        const message = inputField.value.trim();
        if (!message) return;
        addMessage("You", message);
        inputField.value = "";

        fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message })
        })
        .then(response => response.json())
        .then(data => {
            addMessage("Bot", data.reply);
        })
        .catch(error => {
            addMessage("Bot", "Error: Could not fetch response.");
        });
    }

    function addMessage(sender, text) {
        let messageElement = document.createElement("p");
        messageElement.innerHTML = `<strong>${sender}:</strong> ${text}`;
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
