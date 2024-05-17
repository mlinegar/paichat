const ws = new WebSocket(`ws://${window.location.host}/chat`);
const messagesDiv = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-button');

console.log('WebSocket connection established');

ws.onopen = () => {
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
            currentResponseDiv.textContent = 'Bot: ';
            currentResponseDiv.id = `response-${message.message_id}`;
            messagesDiv.appendChild(currentResponseDiv);
        }
        currentResponseDiv.textContent += message.data;

        if (message.complete) {
            currentResponseDiv = null;
            responseMessageId = null;
            console.log('Response complete');
        }
        console.log('Appended response to messages');
    }
};

ws.onerror = (error) => {
    console.error('WebSocket error observed:', error);
};

ws.onclose = (event) => {
    console.log('WebSocket connection closed:', event);
};

sendButton.onclick = () => {
    const text = userInput.value;
    const userDiv = document.createElement('div');
    userDiv.textContent = `You: ${text}`;
    messagesDiv.appendChild(userDiv);
    console.log(`Sent message: ${text}`);

    ws.send(JSON.stringify({ type: 'input', text: text }));
    userInput.value = '';
};

userInput.onkeydown = (event) => {
    if (event.key === 'Enter') {
        sendButton.click();
    }
};
// const ws = new WebSocket(`ws://${window.location.host}/chat`);
// const messagesDiv = document.getElementById('messages');
// const userInput = document.getElementById('user-input');
// const sendButton = document.getElementById('send-button');

// console.log('WebSocket connection established');

// ws.onopen = () => {
//     console.log('WebSocket connection opened');
// };

// let currentResponseDiv = null;

// ws.onmessage = (event) => {
//     console.log('Message received from server');
//     const message = JSON.parse(event.data);
//     console.log('Message data:', message);

//     if (message.type === 'response') {
//         if (!currentResponseDiv) {
//             currentResponseDiv = document.createElement('div');
//             currentResponseDiv.textContent = 'Bot: ';
//             messagesDiv.appendChild(currentResponseDiv);
//         }
//         currentResponseDiv.textContent += message.data;

//         if (message.complete) {
//             currentResponseDiv = null;
//             console.log('Response complete');
//         }
//         console.log('Appended response to messages');
//     }
// };

// ws.onerror = (error) => {
//     console.error('WebSocket error observed:', error);
// };

// ws.onclose = (event) => {
//     console.log('WebSocket connection closed:', event);
// };

// sendButton.onclick = () => {
//     const text = userInput.value;
//     const userDiv = document.createElement('div');
//     userDiv.textContent = `You: ${text}`;
//     messagesDiv.appendChild(userDiv);
//     console.log(`Sent message: ${text}`);

//     ws.send(JSON.stringify({ type: 'input', text: text }));
//     userInput.value = '';
// };

// userInput.onkeydown = (event) => {
//     if (event.key === 'Enter') {
//         sendButton.click();
//     }
// };

// const ws = new WebSocket(`ws://${window.location.host}/chat`);
// const messagesDiv = document.getElementById('messages');
// const userInput = document.getElementById('user-input');
// const sendButton = document.getElementById('send-button');

// console.log('WebSocket connection established');

// ws.onopen = () => {
//     console.log('WebSocket connection opened');
// };

// ws.onmessage = (event) => {
//     console.log('Message received from server');
//     const message = JSON.parse(event.data);
//     console.log('Message data:', message);
//     if (message.type === 'response') {
//         let responseDiv = document.getElementById('response');
//         if (!responseDiv) {
//             responseDiv = document.createElement('div');
//             responseDiv.id = 'response';
//             responseDiv.textContent = `Bot: ${message.data}`;
//             messagesDiv.appendChild(responseDiv);
//         } else {
//             responseDiv.textContent += message.data;
//         }
//         if (message.complete) {
//             responseDiv = null;
//             console.log('Response complete');
//         }
//         console.log('Appended response to messages');
//     }
// };

// ws.onerror = (error) => {
//     console.error('WebSocket error observed:', error);
// };

// ws.onclose = (event) => {
//     console.log('WebSocket connection closed:', event);
// };

// sendButton.onclick = () => {
//     const text = userInput.value;
//     const userDiv = document.createElement('div');
//     userDiv.textContent = `You: ${text}`;
//     messagesDiv.appendChild(userDiv);
//     console.log(`Sent message: ${text}`);

//     ws.send(JSON.stringify({ type: 'input', text: text }));
//     userInput.value = '';
// };

// userInput.onkeydown = (event) => {
//     if (event.key === 'Enter') {
//         sendButton.click();
//     }
// };
