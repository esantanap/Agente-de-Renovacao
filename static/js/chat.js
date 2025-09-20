// Estado da aplicação
let currentCpf = '';
let chatHistory = [];
let isAnalyzing = false;

// Elementos DOM
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const loadingIndicator = document.getElementById('loadingIndicator');
const quickActions = document.getElementById('quickActions');

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    updateCurrentTime();
    setupEventListeners();
    loadChatHistory();
});

// Event listeners
function setupEventListeners() {
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keypress', handleKeyPress);
    sendButton.addEventListener('click', sendMessage);
}

function handleInputChange() {
    const value = messageInput.value.trim();
    sendButton.disabled = value.length === 0 || isAnalyzing;
    
    // Auto-detectar CPF
    const cpfPattern = /\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2}/;
    if (cpfPattern.test(value)) {
        currentCpf = value.replace(/\D/g, '');
        showSuggestions();
    }
}

function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey && !sendButton.disabled) {
        e.preventDefault();
        sendMessage();
    }
}

// Funções de mensagem
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isAnalyzing) return;
    
    // Adicionar mensagem do usuário
    addMessage(message, 'user');
    messageInput.value = '';
    sendButton.disabled = true;
    
    // Detectar se é CPF ou pergunta
    const cpfPattern = /\d{11}|\d{3}\.\d{3}\.\d{3}-\d{2}/;
    const cpfMatch = message.match(cpfPattern);
    
    if (cpfMatch) {
        currentCpf = cpfMatch[0].replace(/\D/g, '');
        await analyzeClient(currentCpf, 'Este cliente possui impedimentos para renovação?');
    } else if (currentCpf) {
        await analyzeClient(currentCpf, message);
    } else {
        addMessage('Por favor, primeiro informe o CPF do cliente que deseja analisar.', 'bot');
    }
    
    hideQuickActions();
}

function sendQuickMessage(cpf) {
    messageInput.value = cpf;
    sendMessage();
}

function applySuggestion(suggestion) {
    if (currentCpf) {
        messageInput.value = suggestion;
        messageInput.focus();
    } else {
        showToast('Primeiro informe um CPF válido', 'warning');
    }
}

// Análise do cliente
async function analyzeClient(cpf, pergunta) {
    if (isAnalyzing) return;
    
    isAnalyzing = true;
    showLoading();
    
    try {
        const response = await fetch('/api/v1/analisar', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                cpf: cpf,
                pergunta: pergunta
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayAnalysisResult(data);
            showToast('Análise concluída com sucesso!', 'success');
        } else {
            handleAnalysisError(data);
        }
        
    } catch (error) {
        console.error('Erro na análise:', error);
        addMessage('❌ Erro ao conectar com o servidor. Tente novamente.', 'bot');
        showToast('Erro de conexão', 'error');
    } finally {
        isAnalyzing = false;
        hideLoading();
        sendButton.disabled = false;
    }
}

function displayAnalysisResult(data) {
    const { cpf, decisao, justificativa, detalhes } = data;
    
    // Criar mensagem com resultado
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot-message';
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<i class="fas fa-robot"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    
    // Cabeçalho da análise
    const analysisResult = document.createElement('div');
    analysisResult.className = `analysis-result ${decisao.toLowerCase()}`;
    
    const header = document.createElement('div');
    header.className = 'analysis-header';
    
    const icon = getDecisionIcon(decisao);
    header.innerHTML = `${icon} <strong>Análise do CPF ${formatCpf(cpf)}</strong>`;
    
    const details = document.createElement('div');
    details.className = 'analysis-details';
    details.innerHTML = `
        <p><strong>Decisão:</strong> ${decisao}</p>
        <p><strong>Cliente:</strong> ${detalhes.nome || 'Não informado'}</p>
        <hr style="margin: 0.75rem 0; border: none; border-top: 1px solid rgba(0,0,0,0.1);">
        <p>${justificativa}</p>
    `;
    
    if (detalhes.impedimentos && detalhes.impedimentos.length > 0) {
        details.innerHTML += `
            <p style="margin-top: 0.75rem;"><strong>Impedimentos:</strong></p>
            <ul style="margin-left: 1rem;">
                ${detalhes.impedimentos.map(imp => `<li>${imp}</li>`).join('')}
            </ul>
        `;
    }
    
    if (detalhes.ajustes && detalhes.ajustes.length > 0) {
        details.innerHTML += `
            <p style="margin-top: 0.75rem;"><strong>Ajustes Necessários:</strong></p>
            <ul style="margin-left: 1rem;">
                ${detalhes.ajustes.map(ajuste => `<li>${ajuste}</li>`).join('')}
            </ul>
        `;
    }
    
    analysisResult.appendChild(header);
    analysisResult.appendChild(details);
    bubble.appendChild(analysisResult);
    
    const time = document.createElement('div');
    time.className = 'message-time';
    time.innerHTML = `<span>${getCurrentTime()}</span>`;
    
    content.appendChild(bubble);
    content.appendChild(time);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
    
    // Salvar no histórico
    saveChatHistory();
}

function handleAnalysisError(error) {
    let errorMessage = '❌ Erro na análise: ';
    
    if (error.detail) {
        if (error.detail.includes('não encontrado')) {
            errorMessage += 'Cliente não encontrado no banco de dados.';
        } else if (error.detail.includes('CPF inválido')) {
            errorMessage += 'CPF informado é inválido.';
        } else {
            errorMessage += error.detail;
        }
    } else {
        errorMessage += 'Erro interno do servidor.';
    }
    
    addMessage(errorMessage, 'bot');
    showToast('Erro na análise', 'error');
}

// Funções auxiliares
function addMessage(text, sender) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = sender === 'bot' ? '<i class="fas fa-robot"></i>' : '<i class="fas fa-user"></i>';
    
    const content = document.createElement('div');
    content.className = 'message-content';
    
    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = `<p>${text}</p>`;
    
    const time = document.createElement('div');
    time.className = 'message-time';
    time.innerHTML = `<span>${getCurrentTime()}</span>`;
    
    content.appendChild(bubble);
    content.appendChild(time);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(content);
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function getDecisionIcon(decisao) {
    switch (decisao.toLowerCase()) {
        case 'aprovável':
            return '✅';
        case 'ressalvas':
            return '⚠️';
        case 'impedida':
            return '❌';
        default:
            return '📊';
    }
}

function formatCpf(cpf) {
    return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

function getCurrentTime() {
    return new Date().toLocaleTimeString('pt-BR', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

function updateCurrentTime() {
    const timeElement = document.getElementById('currentTime');
    if (timeElement) {
        timeElement.textContent = getCurrentTime();
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showLoading() {
    loadingIndicator.style.display = 'flex';
}

function hideLoading() {
    loadingIndicator.style.display = 'none';
}

function showSuggestions() {
    // Mostrar sugestões quando CPF for detectado
    const suggestions = document.getElementById('inputSuggestions');
    if (suggestions) {
        suggestions.style.display = 'flex';
    }
}

function hideQuickActions() {
    quickActions.style.display = 'none';
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `<p>${message}</p>`;
    
    const container = document.getElementById('toastContainer');
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Funções de tema e limpeza
function toggleTheme() {
    const body = document.body;
    const currentTheme = body.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    body.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    const icon = document.querySelector('.header-actions .btn-icon i');
    icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
}

function clearChat() {
    if (confirm('Tem certeza que deseja limpar a conversa?')) {
        chatMessages.innerHTML = `
            <div class="message bot-message">
                <div class="message-avatar">
                    <i class="fas fa-robot"></i>
                </div>
                <div class="message-content">
                    <div class="message-bubble">
                        <p>👋 Conversa limpa! Pronto para uma nova análise.</p>
                        <p>Digite o <strong>CPF do cliente</strong> que deseja analisar.</p>
                    </div>
                    <div class="message-time">
                        <span>${getCurrentTime()}</span>
                    </div>
                </div>
            </div>
        `;
        currentCpf = '';
        quickActions.style.display = 'flex';
        localStorage.removeItem('chatHistory');
    }
}

// Persistência do chat
function saveChatHistory() {
    const messages = Array.from(chatMessages.children).map(msg => ({
        html: msg.outerHTML,
        timestamp: Date.now()
    }));
    localStorage.setItem('chatHistory', JSON.stringify(messages));
}

function loadChatHistory() {
    const saved = localStorage.getItem('chatHistory');
    if (saved) {
        const messages = JSON.parse(saved);
        // Carregar apenas mensagens das últimas 24 horas
        const dayAgo = Date.now() - (24 * 60 * 60 * 1000);
        const recentMessages = messages.filter(msg => msg.timestamp > dayAgo);
        
        if (recentMessages.length > 0) {
            chatMessages.innerHTML = recentMessages.map(msg => msg.html).join('');
            scrollToBottom();
        }
    }
}

// Carregar tema salvo
document.addEventListener('DOMContentLoaded', function() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.body.setAttribute('data-theme', savedTheme);
        const icon = document.querySelector('.header-actions .btn-icon i');
        if (icon) {
            icon.className = savedTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
});