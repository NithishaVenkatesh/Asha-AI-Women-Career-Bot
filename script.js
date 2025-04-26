document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const uploadButton = document.getElementById('upload-btn');
    const resumeUpload = document.getElementById('resume-upload');
    const uploadProgress = document.querySelector('.upload-progress');
    const progressFill = document.querySelector('.progress-fill');
    const fileName = document.querySelector('.file-name');
    let isProcessing = false;

    // Voice recognition setup
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US'; // Default language

    // Speech synthesis setup
    const synthesis = window.speechSynthesis;
    let currentVoice = null;

    // Function to initialize speech synthesis voices
    function initVoices() {
        const voices = synthesis.getVoices();
        currentVoice = voices.find(voice => voice.lang === 'en-US') || voices[0];
    }

    // Initialize voices when they're loaded
    if (synthesis.getVoices().length > 0) {
        initVoices();
    } else {
        synthesis.onvoiceschanged = initVoices;
    }

    // Function to detect language from text
    async function detectLanguage(text) {
        try {
            const response = await fetch('/detect-language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text }),
            });
            const data = await response.json();
            return data.language;
        } catch (error) {
            console.error('Language detection error:', error);
            return 'en-US';
        }
    }

    // Function to speak text
    function speakText(text, lang = 'en-US') {
        if (synthesis.speaking) {
            synthesis.cancel();
        }

        const utterance = new SpeechSynthesisUtterance(text);
        utterance.voice = currentVoice;
        utterance.lang = lang;
        synthesis.speak(utterance);
    }

    // Function to start voice input
    function startVoiceInput() {
        recognition.start();
        userInput.placeholder = 'Listening...';
        userInput.disabled = true;
        sendButton.disabled = true;
    }

    // Function to stop voice input
    function stopVoiceInput() {
        recognition.stop();
        userInput.placeholder = 'Type your message...';
        userInput.disabled = false;
        sendButton.disabled = false;
    }

    // Handle voice recognition results
    recognition.onresult = async (event) => {
        const text = event.results[0][0].transcript;
        userInput.value = text;
        stopVoiceInput();
        
        // Detect language and update recognition
        const detectedLang = await detectLanguage(text);
        recognition.lang = detectedLang;
        
        // Send the message
        handleSendMessage();
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        stopVoiceInput();
        addMessage("Sorry, I couldn't understand that. Please try again or type your message.");
    };

    // Add voice control buttons to the UI
    const voiceControls = document.createElement('div');
    voiceControls.className = 'voice-controls';
    voiceControls.innerHTML = `
        <button id="voice-input-btn" class="voice-btn" title="Start voice input">
            <i class="fas fa-microphone"></i>
        </button>
        <button id="voice-output-btn" class="voice-btn" title="Toggle voice output">
            <i class="fas fa-volume-up"></i>
        </button>
    `;

    // Insert voice controls just before the chat input area
    const chatInput = document.querySelector('.chat-input');
    if (chatInput && chatInput.parentNode) {
        chatInput.parentNode.insertBefore(voiceControls, chatInput);
    } else {
        console.error('Chat input area not found');
    }

    // Voice control event listeners
    const voiceInputBtn = document.getElementById('voice-input-btn');
    const voiceOutputBtn = document.getElementById('voice-output-btn');

    if (voiceInputBtn) {
        voiceInputBtn.addEventListener('click', () => {
            if (recognition.started) {
                stopVoiceInput();
                voiceInputBtn.classList.remove('active');
            } else {
                startVoiceInput();
                voiceInputBtn.classList.add('active');
            }
        });
    }

    if (voiceOutputBtn) {
        let voiceOutputEnabled = true;
        voiceOutputBtn.addEventListener('click', () => {
            voiceOutputEnabled = !voiceOutputEnabled;
            voiceOutputBtn.innerHTML = voiceOutputEnabled ? 
                '<i class="fas fa-volume-up"></i>' : 
                '<i class="fas fa-volume-mute"></i>';
            voiceOutputBtn.classList.toggle('active', !voiceOutputEnabled);
        });
    }

    // Function to create a clickable link
    function createLink(url) {
        const link = document.createElement('a');
        link.href = url;
        link.textContent = url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        return link;
    }

    // Function to add a message to the chat
    function addMessage(message, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isUser ? 'user-message' : 'asha-message'}`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Split message by newlines and create paragraphs
        const paragraphs = message.split('\n');
        paragraphs.forEach(paragraph => {
            if (paragraph.trim()) {
                const p = document.createElement('p');
                
                // Check if the line contains a URL
                if (paragraph.includes('🔗')) {
                    const [label, url] = paragraph.split('Link: ');
                    p.textContent = label + 'Link: ';
                    p.appendChild(createLink(url.trim()));
                } else {
                    // Handle markdown-style bold text
                    const boldPattern = /\*\*(.*?)\*\*/g;
                    let lastIndex = 0;
                    let match;
                    let textContent = '';
                    
                    while ((match = boldPattern.exec(paragraph)) !== null) {
                        // Add text before the bold part
                        textContent += paragraph.substring(lastIndex, match.index);
                        
                        // Add the bold text
                        const bold = document.createElement('strong');
                        bold.textContent = match[1];
                        p.appendChild(document.createTextNode(textContent));
                        p.appendChild(bold);
                        
                        textContent = '';
                        lastIndex = boldPattern.lastIndex;
                    }
                    
                    // Add any remaining text
                    textContent += paragraph.substring(lastIndex);
                    if (textContent) {
                        p.appendChild(document.createTextNode(textContent));
                    }
                }
                
                messageContent.appendChild(p);
            }
        });
        
        messageDiv.appendChild(messageContent);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        if (!isUser && voiceOutputEnabled) {
            speakText(message);
        }
    }

    // Function to show upload progress
    function showUploadProgress(file) {
        fileName.textContent = file.name;
        uploadProgress.style.display = 'block';
        progressFill.style.width = '0%';
    }

    // Function to update upload progress
    function updateUploadProgress(percent) {
        progressFill.style.width = `${percent}%`;
    }

    // Function to hide upload progress
    function hideUploadProgress() {
        setTimeout(() => {
            uploadProgress.style.display = 'none';
            progressFill.style.width = '0%';
        }, 1000);
    }

    // Function to handle file upload
    async function handleFileUpload(file) {
        if (!file) return;

        showUploadProgress(file);
        updateUploadProgress(20);

        // Add a message to show the upload is happening
        addMessage("I'm uploading and analyzing your resume. Please wait a moment... 📄", true);

        const formData = new FormData();
        formData.append('resume', file);

        try {
            updateUploadProgress(50);
            const response = await fetch('/upload-resume', {
                method: 'POST',
                body: formData
            });

            updateUploadProgress(80);
            const data = await response.json();
            
            if (data.success) {
                // Add bot's response
                addMessage(data.response);
            } else {
                // Show error message
                addMessage(`Sorry, I couldn't process your resume: ${data.error || 'Unknown error'}. Please try again.`);
            }
            updateUploadProgress(100);
        } catch (error) {
            console.error('Upload error:', error);
            addMessage("I'm sorry, I encountered an error while processing your resume. Please try again.");
        } finally {
            hideUploadProgress();
        }
    }

    // Function to send message to backend
    async function sendMessage(message) {
        if (isProcessing) return;
        isProcessing = true;
        
        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
            });

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            return data.response;
        } catch (error) {
            console.error('Error:', error);
            return "I'm sorry, I encountered an error. Please try again later.";
        } finally {
            isProcessing = false;
        }
    }

    // Function to handle sending messages
    async function handleSendMessage() {
        const message = userInput.value.trim();
        if (message && !isProcessing) {
            // Add user message to chat
            addMessage(message, true);
            userInput.value = '';
            userInput.disabled = true;
            sendButton.disabled = true;

            // Send to backend and get response
            const response = await sendMessage(message);
            addMessage(response);

            // Re-enable input
            userInput.disabled = false;
            sendButton.disabled = false;
            userInput.focus();
        }
    }

    // Handle upload button click
    uploadButton.addEventListener('click', () => {
        resumeUpload.click();
    });

    // Handle resume file selection
    resumeUpload.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.size > 16 * 1024 * 1024) { // 16MB limit
                addMessage("Sorry, the file is too large. Please upload a file smaller than 16MB.");
                return;
            }
            handleFileUpload(file);
        }
        // Clear the input
        e.target.value = '';
    });

    // Handle send button click
    sendButton.addEventListener('click', handleSendMessage);

    // Handle Enter key
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Focus input on load
    userInput.focus();

    // Add initial bot message
    addMessage("Hello! 👋 I'm Asha, your AI career companion. I can help you with career advice, job search, and resume analysis. Feel free to ask me anything or upload your resume for a detailed review! 💼");
}); 