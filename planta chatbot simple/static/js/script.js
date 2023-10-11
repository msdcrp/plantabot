function displayUserMessage(message) {
    const chatbox = document.getElementById("chatbox");
    const userMessageDiv = document.createElement("div");
    userMessageDiv.className = "user-message";
    userMessageDiv.innerHTML = `<p>${message}</p>`;
    chatbox.appendChild(userMessageDiv);
    scrollToBottom();
}

function displayBotMessage(message) {
    const chatbox = document.getElementById("chatbox");
    const botMessageDiv = document.createElement("div");
    botMessageDiv.className = "bot-message";
    botMessageDiv.innerHTML = `<p>${message}</p>`;
    chatbox.appendChild(botMessageDiv);
    scrollToBottom();
}

function scrollToBottom() {
    const chatbox = document.getElementById("chatbox");
    chatbox.scrollTop = chatbox.scrollHeight;
}

function handleBotResponse(response) {
    if (response.reply.toLowerCase().includes("welcome")) {
        displayBotMessage("Great! Let's get started. What's your name?");
    } else {
        displayBotMessage(response.reply);
    }
}

function sendMessage() {
    const messageInput = document.getElementById("message");
    const userMessage = messageInput.value;
    displayUserMessage(userMessage);
    messageInput.value = "";

    fetch("/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userMessage })
    })
    .then(response => response.json())
    .then(data => handleBotResponse(data))
    .catch(error => console.error("Error:", error));
}

// Event listener for the ENTER key
document.getElementById("message").addEventListener("keydown", function(event) {
    if (event.keyCode === 13 && !event.shiftKey) {  // 13 is the ENTER key's code
        event.preventDefault();  // Prevents the default action (newline)
        sendMessage();  // Send the message
    }
});
