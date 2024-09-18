const ws = new WebSocket(`ws://${window.location.host}/chat`);
const messagesDiv = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');
const stopButton = document.getElementById('stop-chat');

// let userMessageCount = 0; // Initialize message count

console.log('WebSocket connection established');

// ws.onopen = () => {
//     console.log('WebSocket connection opened');
// };
window.ws.onopen = () => {
    console.log('WebSocket connection opened');
};

let currentResponseDiv = null;
let responseMessageId = null;

ws.onmessage = (event) => {
    console.log('Message received from server');
    const message = JSON.parse(event.data);
    console.log('Message data:', message);

    if (message.type === 'response') {
        if (responseMessageId !== message.message_id) {
            responseMessageId = message.message_id;
            currentResponseDiv = document.createElement('div');
            currentResponseDiv.className = 'message assistant';
            messagesDiv.appendChild(currentResponseDiv);
        }

        currentResponseDiv.textContent += message.data;

        if (message.complete) {
            currentResponseDiv = null;
            responseMessageId = null;
            console.log('Response complete');
        
            if (message.end_script) {
                console.log('Script ended. Redirecting to survey.');
                setTimeout(() => {
                    window.location.href = 'chat_assets/survey-complete.html';
                }, 5000);  // Redirect after 5 seconds
            } else {
                // Focus on the input field after a short delay
                setTimeout(() => {
                    userInput.focus();
                }, 100);
            }
        }
        console.log('Appended response to messages');
        messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to the bottom
    }
};

// ws.onmessage = (event) => {
//     console.log('Message received from server');
//     const message = JSON.parse(event.data);
//     console.log('Message data:', message);

//     if (message.type === 'response') {
//         if (responseMessageId !== message.message_id) {
//             responseMessageId = message.message_id;
//             currentResponseDiv = document.createElement('div');
//             currentResponseDiv.className = 'message assistant';
//             messagesDiv.appendChild(currentResponseDiv);
//         }

//         const contentDiv = document.createElement('div');
//         contentDiv.className = 'message-content';
//         contentDiv.textContent = message.data;
//         currentResponseDiv.appendChild(contentDiv);

//         if (message.complete) {
//             currentResponseDiv = null;
//             responseMessageId = null;
//             console.log('Response complete');

//             if (message.end_script) {
//                 console.log('Script ended. Creating survey link.');
//                 const surveyUrl = message.data.split('please go to: ')[1];
//                 if (surveyUrl) {
//                     const linkDiv = document.createElement('div');
//                     linkDiv.className = 'survey-link';
//                     const link = document.createElement('a');
//                     link.href = surveyUrl;
//                     link.textContent = 'Complete the Survey';
//                     link.target = '_blank';
//                     linkDiv.appendChild(link);
//                     messagesDiv.appendChild(linkDiv);
//                 }
//             }
//         }
//         console.log('Appended response to messages');
//         messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to the bottom
//     }
// };
// ws.onmessage = (event) => {
//     console.log('Message received from server');
//     const message = JSON.parse(event.data);
//     console.log('Message data:', message);

//     if (message.type === 'response') {
//         if (responseMessageId !== message.message_id) {
//             responseMessageId = message.message_id;
//             currentResponseDiv = document.createElement('div');
//             currentResponseDiv.className = 'message assistant';
//             messagesDiv.appendChild(currentResponseDiv);
//         }

//         const contentDiv = document.createElement('div');
//         contentDiv.className = 'message-content';
//         contentDiv.innerHTML = message.data; // Use innerHTML to render HTML content
//         currentResponseDiv.appendChild(contentDiv);

//         if (message.complete) {
//             currentResponseDiv = null;
//             responseMessageId = null;
//             console.log('Response complete');

//             if (message.end_script) {
//                 console.log('Script ended. Survey link provided.');
//                 // Optionally, you can add additional UI feedback here
//             }
//         }
//         console.log('Appended response to messages');
//         messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to the bottom
//     }
// };

// ws.onmessage = (event) => {
//     console.log('Message received from server');
//     const message = JSON.parse(event.data);
//     console.log('Message data:', message);

//     if (message.type === 'response') {
//         if (responseMessageId !== message.message_id) {
//             responseMessageId = message.message_id;
//             currentResponseDiv = document.createElement('div');
//             currentResponseDiv.textContent = 'Bot: ';
//             currentResponseDiv.id = `response-${message.message_id}`;
//             messagesDiv.appendChild(currentResponseDiv);
//         }
//         currentResponseDiv.textContent += message.data;

//         if (message.complete) {
//             currentResponseDiv = null;
//             responseMessageId = null;
//             console.log('Response complete');

//             if (message.end_script) {
//                 console.log('Script ended. Survey link provided.');
//                 // Optionally, you can add additional UI feedback here
//             }
//         }
//         console.log('Appended response to messages');
//         messagesDiv.scrollTop = messagesDiv.scrollHeight; // Auto-scroll to the bottom
//     }
// };

ws.onerror = (error) => {
    console.error('WebSocket error observed:', error);
};

ws.onclose = (event) => {
    console.log('WebSocket connection closed:', event);
};

// sendButton.onclick = () => {
//     const text = userInput.value;
//     const userDiv = document.createElement('div');
//     userDiv.textContent = `You: ${text}`;
//     messagesDiv.appendChild(userDiv);
//     console.log(`Sent message: ${text}`);

//     ws.send(JSON.stringify({ type: 'input', text: text }));
//     userInput.value = '';


//     userMessageCount++; // Increment message count
//     updateStopButton(); // Update stop button state
// };

// function updateStopButton() {
//     stopButton.disabled = userMessageCount < 3;
// }


// function handleStopChat() {
//     if (userMessageCount >= 3) {
//         stopChat();
//     } else {
//         alert("Please send at least 3 messages before stopping the chat.");
//     }
// }

// function stopChat() {
//     if (ws && ws.readyState === WebSocket.OPEN) {
//         ws.close();
//     }
//     window.location.href = 'chat_assets/survey-complete.html';
// }

// userInput.onkeydown = (event) => {
//     if (event.key === 'Enter') {
//         sendButton.click();
//     }
// };


function sendMessage(text) {
    const userDiv = document.createElement('div');
    userDiv.className = 'message user';
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = text;
    userDiv.appendChild(contentDiv);
    messagesDiv.appendChild(userDiv);
    console.log(`Sent message: ${text}`);

    ws.send(JSON.stringify({ type: 'input', text: text }));
    userInput.value = '';
    
    // Call the function defined in index.html to increment the message count
    incrementMessageCount();
    // Scroll to the bottom of the messages div
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

userInput.onkeydown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendButton.click();
    }
};


// Function to handle window resize and orientation change
function handleResize() {
    // Adjust the height of the messages div to account for the keyboard
    const windowHeight = window.innerHeight;
    const toolbarHeight = document.querySelector('.toolbar').offsetHeight;
    const inputHeight = document.querySelector('.input').offsetHeight;
    messagesDiv.style.height = `${windowHeight - toolbarHeight - inputHeight}px`;
}

// Add event listeners for resize and orientation change
window.addEventListener('resize', handleResize);
window.addEventListener('orientationchange', handleResize);

// Initial call to set the correct height
handleResize();

// Function to attempt refocusing the input field
function attemptRefocus() {
    if (document.activeElement !== userInput) {
        userInput.focus();
    }
}

// Add touch event listeners to the document
document.addEventListener('touchstart', attemptRefocus);
document.addEventListener('touchend', attemptRefocus);