// Sistema de pagos y límite de análisis gratuitos

// Estado del usuario
let userState = {
    remainingAnalyses: 5,
    isPremium: false,
    userId: null,
    sessionId: null
};

// Inicializar sistema de pagos
function initializePaymentSystem() {
    // Generar ID de sesión único
    userState.sessionId = generateSessionId();
    userState.userId = getUserId();
    
    // Cargar estado desde localStorage si existe
    loadUserState();
    
    // Actualizar UI
    updateAnalysisCounter();
    
    // Mostrar bienvenida si es primera vez
    if (isFirstVisit()) {
        showWelcomeMessage();
    }
}

// Generar ID de sesión único
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Obtener ID de usuario (basado en IP o localStorage)
function getUserId() {
    let userId = localStorage.getItem('feeliPet_userId');
    if (!userId) {
        userId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('feeliPet_userId', userId);
    }
    return userId;
}

// Cargar estado del usuario
function loadUserState() {
    try {
        const savedState = localStorage.getItem('feeliPet_userState');
        if (savedState) {
            const parsed = JSON.parse(savedState);
            userState = { ...userState, ...parsed };
            
            // Verificar si el estado es de hoy (reset diario opcional)
            const today = new Date().toDateString();
            const lastUsage = parsed.lastUsage;
            
            if (lastUsage && lastUsage !== today && !userState.isPremium) {
                // Reset diario para usuarios gratuitos (opcional)
                // userState.remainingAnalyses = 5;
            }
        }
    } catch (error) {
        console.error('Error cargando estado del usuario:', error);
    }
}

// Guardar estado del usuario
function saveUserState() {
    try {
        userState.lastUsage = new Date().toDateString();
        localStorage.setItem('feeliPet_userState', JSON.stringify(userState));
    } catch (error) {
        console.error('Error guardando estado del usuario:', error);
    }
}

// Verificar si es primera visita
function isFirstVisit() {
    return !localStorage.getItem('feeliPet_hasVisited');
}

// Marcar como visitado
function markAsVisited() {
    localStorage.setItem('feeliPet_hasVisited', 'true');
}

// Verificar si puede hacer análisis
function canAnalyze() {
    return userState.isPremium || userState.remainingAnalyses > 0;
}

// Consumir un análisis
function consumeAnalysis() {
    if (userState.isPremium) {
        return true; // Usuario premium, sin límites
    }
    
    if (userState.remainingAnalyses > 0) {
        userState.remainingAnalyses--;
        saveUserState();
        updateAnalysisCounter();
        
        // Mostrar modal de upgrade si quedan pocos intentos
        if (userState.remainingAnalyses <= 2 && userState.remainingAnalyses > 0) {
            showUpgradeReminder();
        }
        
        // Mostrar modal de pago si se acabaron los intentos
        if (userState.remainingAnalyses === 0) {
            setTimeout(showPaymentModal, 2000); // Mostrar después de ver resultados
        }
        
        return true;
    }
    
    return false;
}

// Actualizar contador en la UI
function updateAnalysisCounter() {
    const counter = document.getElementById('analysisCounter');
    const progressBar = document.getElementById('analysisProgressBar');
    const statusText = document.getElementById('analysisStatusText');
    
    if (userState.isPremium) {
        if (counter) counter.innerHTML = '♾️ Análisis Ilimitados';
        if (progressBar) progressBar.style.width = '100%';
        if (statusText) statusText.innerHTML = '🌟 Usuario Premium';
    } else {
        if (counter) counter.innerHTML = `${userState.remainingAnalyses}/5 Análisis Gratuitos`;
        if (progressBar) {
            const percentage = (userState.remainingAnalyses / 5) * 100;
            progressBar.style.width = `${percentage}%`;
            
            // Cambiar color según el nivel
            if (percentage > 60) {
                progressBar.style.background = '#00FFB7';
            } else if (percentage > 20) {
                progressBar.style.background = '#FFB700';
            } else {
                progressBar.style.background = '#FF6B6B';
            }
        }
        if (statusText) {
            if (userState.remainingAnalyses === 0) {
                statusText.innerHTML = '⚠️ Límite alcanzado - Desbloquea acceso completo';
                statusText.style.color = '#FF6B6B';
            } else if (userState.remainingAnalyses <= 2) {
                statusText.innerHTML = '⏰ Quedan pocos análisis gratuitos';
                statusText.style.color = '#FFB700';
            } else {
                statusText.innerHTML = '✅ Análisis gratuitos disponibles';
                statusText.style.color = '#00FFB7';
            }
        }
    }
}

// Mostrar mensaje de bienvenida
function showWelcomeMessage() {
    const modal = createModal('welcome', {
        title: '🐕 ¡Bienvenido a FeeliPet!',
        content: `
            <div class="welcome-content">
                <div class="welcome-icon">🎉</div>
                <h3>Tu Monitor Inteligente de Emociones Caninas</h3>
                <p>Analiza las emociones de tu perro usando Inteligencia Artificial avanzada.</p>
                
                <div class="feature-highlights">
                    <div class="feature-item">
                        <span class="feature-icon">🧠</span>
                        <span>IA Avanzada</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📊</span>
                        <span>Análisis Detallado</span>
                    </div>
                    <div class="feature-item">
                        <span class="feature-icon">📱</span>
                        <span>Bot de Telegram</span>
                    </div>
                </div>
                
                <div class="trial-info">
                    <h4>🎁 Prueba Gratuita</h4>
                    <p>Comienza con <strong>5 análisis gratuitos</strong> para probar todas las funcionalidades.</p>
                    <div class="trial-counter">
                        <div class="trial-dots">
                            ${'<span class="dot active"></span>'.repeat(5)}
                        </div>
                        <span>5 análisis incluidos</span>
                    </div>
                </div>
            </div>
        `,
        buttons: [
            {
                text: '¡Comenzar Ahora!',
                class: 'btn-primary',
                action: () => {
                    closeModal('welcome');
                    markAsVisited();
                    // Scroll al upload section
                    document.getElementById('uploadSection')?.scrollIntoView({ behavior: 'smooth' });
                }
            }
        ]
    });
    
    showModal(modal);
}

// Mostrar recordatorio de upgrade
function showUpgradeReminder() {
    if (document.getElementById('upgradeReminder')) return; // Ya se mostró
    
    const reminder = document.createElement('div');
    reminder.id = 'upgradeReminder';
    reminder.className = 'upgrade-reminder';
    reminder.innerHTML = `
        <div class="reminder-content">
            <div class="reminder-icon">⚠️</div>
            <div class="reminder-text">
                <strong>Quedan ${userState.remainingAnalyses} análisis gratuitos</strong>
                <p>Desbloquea acceso ilimitado para tu mascota</p>
            </div>
            <button class="btn-upgrade" onclick="showPaymentModal()">
                🌟 Desbloquear Ahora
            </button>
            <button class="btn-close" onclick="closeUpgradeReminder()">×</button>
        </div>
    `;
    
    document.body.appendChild(reminder);
    
    // Auto-cerrar después de 10 segundos
    setTimeout(() => {
        closeUpgradeReminder();
    }, 10000);
}

// Cerrar recordatorio de upgrade
function closeUpgradeReminder() {
    const reminder = document.getElementById('upgradeReminder');
    if (reminder) {
        reminder.remove();
    }
}

// Mostrar modal de pago
function showPaymentModal() {
    const modal = createModal('payment', {
        title: '🌟 Desbloquea FeeliPet Premium',
        content: `
            <div class="payment-content">
                <div class="limit-reached">
                    <div class="limit-icon">🚫</div>
                    <h3>Has alcanzado el límite de análisis gratuitos</h3>
                    <p>Desbloquea acceso completo para monitorear a tu mascota sin restricciones.</p>
                </div>
                
                <div class="premium-benefits">
                    <h4>✨ Beneficios Premium:</h4>
                    <div class="benefits-grid">
                        <div class="benefit-item">
                            <span class="benefit-icon">♾️</span>
                            <div>
                                <strong>Análisis Ilimitados</strong>
                                <p>Sin restricciones de uso</p>
                            </div>
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">📱</span>
                            <div>
                                <strong>Bot Premium de Telegram</strong>
                                <p>Acceso completo a funciones avanzadas</p>
                            </div>
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">📊</span>
                            <div>
                                <strong>Reportes Detallados</strong>
                                <p>Estadísticas completas y recomendaciones personalizadas</p>
                            </div>
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">🔔</span>
                            <div>
                                <strong>Alertas en Tiempo Real</strong>
                                <p>Notificaciones automáticas por Telegram</p>
                            </div>
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">🎥</span>
                            <div>
                                <strong>Videos sin Límite</strong>
                                <p>Analiza videos de cualquier duración</p>
                            </div>
                        </div>
                        <div class="benefit-item">
                            <span class="benefit-icon">💾</span>
                            <div>
                                <strong>Historial Completo</strong>
                                <p>Guarda todos tus análisis</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="pricing-section">
                    <div class="price-card featured">
                        <div class="price-badge">Más Popular</div>
                        <h4>Acceso Completo</h4>
                        <div class="price">
                            <span class="currency">$</span>
                            <span class="amount">9.99</span>
                            <span class="period">único</span>
                        </div>
                        <p class="price-description">Acceso de por vida a todas las funciones</p>
                        <ul class="price-features">
                            <li>✅ Análisis ilimitados</li>
                            <li>✅ Bot de Telegram premium</li>
                            <li>✅ Reportes detallados</li>
                            <li>✅ Alertas automáticas</li>
                            <li>✅ Soporte prioritario</li>
                        </ul>
                    </div>
                </div>
                
                <div class="payment-methods">
                    <h4>💳 Métodos de Pago:</h4>
                    <div class="payment-options">
                        <div class="payment-option" onclick="processPayment('card')">
                            <span class="payment-icon">💳</span>
                            <span>Tarjeta de Crédito/Débito</span>
                        </div>
                        <div class="payment-option" onclick="processPayment('paypal')">
                            <span class="payment-icon">🅿️</span>
                            <span>PayPal</span>
                        </div>
                        <div class="payment-option" onclick="processPayment('crypto')">
                            <span class="payment-icon">₿</span>
                            <span>Criptomonedas</span>
                        </div>
                    </div>
                </div>
                
                <div class="security-info">
                    <p><span class="security-icon">🔒</span> Pago 100% seguro y encriptado</p>
                    <p><span class="security-icon">💝</span> Garantía de satisfacción de 30 días</p>
                </div>
            </div>
        `,
        buttons: [
            {
                text: 'Continuar Gratis Mañana',
                class: 'btn-secondary',
                action: () => closeModal('payment')
            }
        ],
        size: 'large'
    });
    
    showModal(modal);
}

// Procesar pago (simulado)
function processPayment(method) {
    // Simular proceso de pago
    showPaymentProcessing(method);
}

// Mostrar procesamiento de pago
function showPaymentProcessing(method) {
    const modal = createModal('processing', {
        title: '💳 Procesando Pago...',
        content: `
            <div class="processing-content">
                <div class="processing-animation">
                    <div class="spinner"></div>
                </div>
                <h3>Procesando tu pago</h3>
                <p>Método seleccionado: ${getPaymentMethodName(method)}</p>
                <p class="processing-note">No cierres esta ventana...</p>
                
                <div class="processing-steps">
                    <div class="step completed">
                        <span class="step-icon">✅</span>
                        <span>Método de pago verificado</span>
                    </div>
                    <div class="step processing">
                        <span class="step-icon">⏳</span>
                        <span>Procesando transacción...</span>
                    </div>
                    <div class="step pending">
                        <span class="step-icon">⏹️</span>
                        <span>Activando cuenta premium</span>
                    </div>
                </div>
            </div>
        `,
        buttons: [],
        closable: false
    });
    
    showModal(modal);
    
    // Simular proceso (3 segundos)
    setTimeout(() => {
        // Completar segundo paso
        const steps = document.querySelectorAll('.step');
        steps[1].classList.remove('processing');
        steps[1].classList.add('completed');
        steps[1].querySelector('.step-icon').textContent = '✅';
        steps[2].classList.remove('pending');
        steps[2].classList.add('processing');
        
        setTimeout(() => {
            // Completar tercer paso
            steps[2].classList.remove('processing');
            steps[2].classList.add('completed');
            steps[2].querySelector('.step-icon').textContent = '✅';
            
            setTimeout(() => {
                closeModal('processing');
                showPaymentSuccess();
            }, 1000);
        }, 1500);
    }, 2000);
}

// Mostrar éxito del pago
function showPaymentSuccess() {
    // Activar premium
    userState.isPremium = true;
    userState.remainingAnalyses = 999999; // Ilimitado
    saveUserState();
    updateAnalysisCounter();
    
    const modal = createModal('success', {
        title: '🎉 ¡Pago Exitoso!',
        content: `
            <div class="success-content">
                <div class="success-animation">
                    <div class="success-icon">🌟</div>
                    <div class="success-particles"></div>
                </div>
                <h3>¡Bienvenido a FeeliPet Premium!</h3>
                <p>Tu cuenta ha sido activada exitosamente.</p>
                
                <div class="success-benefits">
                    <h4>Ahora tienes acceso a:</h4>
                    <div class="success-list">
                        <div class="success-item">♾️ Análisis ilimitados</div>
                        <div class="success-item">📱 Bot premium de Telegram</div>
                        <div class="success-item">📊 Reportes detallados</div>
                        <div class="success-item">🔔 Alertas automáticas</div>
                    </div>
                </div>
                
                <div class="telegram-access">
                    <h4>🤖 Bot Premium de Telegram</h4>
                    <p>Accede ahora a funciones exclusivas:</p>
                    <button class="btn-telegram" onclick="openTelegramBot()">
                        📱 Abrir Bot Premium
                    </button>
                </div>
            </div>
        `,
        buttons: [
            {
                text: '🚀 Comenzar a Usar Premium',
                class: 'btn-primary',
                action: () => {
                    closeModal('success');
                    // Reload para actualizar la interfaz
                    setTimeout(() => location.reload(), 500);
                }
            }
        ]
    });
    
    showModal(modal);
    
    // Efectos de celebración
    createConfetti();
}

// Obtener nombre del método de pago
function getPaymentMethodName(method) {
    const names = {
        'card': '💳 Tarjeta de Crédito/Débito',
        'paypal': '🅿️ PayPal',
        'crypto': '₿ Criptomonedas'
    };
    return names[method] || 'Método desconocido';
}

// Abrir bot de Telegram
function openTelegramBot() {
    window.open('https://t.me/Emocionesperrunasbot', '_blank');
}

// Sistema de modales genérico
function createModal(id, options) {
    const modal = document.createElement('div');
    modal.id = `modal-${id}`;
    modal.className = `modal-overlay ${options.size || ''}`;
    modal.innerHTML = `
        <div class="modal-content">
            ${options.closable !== false ? '<button class="modal-close" onclick="closeModal(\'' + id + '\')">&times;</button>' : ''}
            <div class="modal-header">
                <h2>${options.title}</h2>
            </div>
            <div class="modal-body">
                ${options.content}
            </div>
            ${options.buttons && options.buttons.length > 0 ? `
                <div class="modal-footer">
                    ${options.buttons.map(btn => `
                        <button class="modal-btn ${btn.class}" onclick="(${btn.action.toString()})()">${btn.text}</button>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
    
    return modal;
}

// Mostrar modal
function showModal(modal) {
    document.body.appendChild(modal);
    document.body.classList.add('modal-open');
    
    // Animación de entrada
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

// Cerrar modal
function closeModal(id) {
    const modal = document.getElementById(`modal-${id}`);
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
            // Verificar si hay otros modales abiertos
            if (!document.querySelector('.modal-overlay')) {
                document.body.classList.remove('modal-open');
            }
        }, 300);
    }
}

// Crear efecto de confetti
function createConfetti() {
    const colors = ['#00FFB7', '#00D4FF', '#6B7AFF', '#FF6B6B', '#FFB700'];
    
    for (let i = 0; i < 100; i++) {
        setTimeout(() => {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.cssText = `
                position: fixed;
                width: 8px;
                height: 8px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                left: ${Math.random() * 100}vw;
                top: -10px;
                z-index: 10000;
                animation: confetti-fall ${2 + Math.random() * 3}s linear forwards;
                transform: rotate(${Math.random() * 360}deg);
            `;
            
            document.body.appendChild(confetti);
            
            setTimeout(() => confetti.remove(), 5000);
        }, i * 20);
    }
}

// Agregar estilos CSS
function addPaymentStyles() {
    if (document.getElementById('payment-styles')) return;
    
    const style = document.createElement('style');
    style.id = 'payment-styles';
    style.textContent = `
        /* Estilos del sistema de pagos */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.3s ease;
            padding: 20px;
        }
        
        .modal-overlay.show {
            opacity: 1;
        }
        
        .modal-overlay.large .modal-content {
            max-width: 800px;
            max-height: 90vh;
            overflow-y: auto;
        }
        
        .modal-content {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            border-radius: 20px;
            padding: 0;
            max-width: 500px;
            width: 100%;
            position: relative;
            border: 2px solid rgba(0, 255, 183, 0.3);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            transform: scale(0.9);
            transition: transform 0.3s ease;
            color: white;
        }
        
        .modal-overlay.show .modal-content {
            transform: scale(1);
        }
        
        .modal-close {
            position: absolute;
            top: 15px;
            right: 20px;
            background: none;
            border: none;
            color: white;
            font-size: 28px;
            cursor: pointer;
            z-index: 1;
            width: 30px;
            height: 30px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            transition: background 0.3s ease;
        }
        
        .modal-close:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .modal-header {
            padding: 30px 30px 20px;
            text-align: center;
        }
        
        .modal-header h2 {
            margin: 0;
            font-size: 1.8rem;
            background: linear-gradient(135deg, #00FFB7 0%, #00D4FF 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .modal-body {
            padding: 0 30px 20px;
        }
        
        .modal-footer {
            padding: 20px 30px 30px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        
        .modal-btn {
            padding: 12px 24px;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
            font-size: 1rem;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #00FFB7 0%, #00D4FF 100%);
            color: #1a1a2e;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 255, 183, 0.4);
        }
        
        .btn-secondary {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            border: 2px solid rgba(255, 255, 255, 0.3);
        }
        
        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.2);
        }
        
        /* Welcome Modal */
        .welcome-content {
            text-align: center;
        }
        
        .welcome-icon {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        
        .feature-highlights {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 30px 0;
        }
        
        .feature-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            padding: 20px 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            border: 1px solid rgba(0, 255, 183, 0.2);
        }
        
        .feature-icon {
            font-size: 2rem;
        }
        
        .trial-info {
            background: rgba(0, 255, 183, 0.1);
            padding: 25px;
            border-radius: 15px;
            margin-top: 30px;
            border: 2px solid rgba(0, 255, 183, 0.3);
        }
        
        .trial-counter {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
            margin-top: 15px;
        }
        
        .trial-dots {
            display: flex;
            gap: 8px;
        }
        
        .dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
        }
        
        .dot.active {
            background: #00FFB7;
            box-shadow: 0 0 10px rgba(0, 255, 183, 0.5);
        }
        
        /* Payment Modal */
        .limit-reached {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: rgba(255, 107, 107, 0.1);
            border-radius: 15px;
            border: 2px solid rgba(255, 107, 107, 0.3);
        }
        
        .limit-icon {
            font-size: 3rem;
            margin-bottom: 15px;
        }
        
        .premium-benefits {
            margin-bottom: 30px;
        }
        
        .benefits-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        
        .benefit-item {
            display: flex;
            align-items: flex-start;
            gap: 15px;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border: 1px solid rgba(0, 255, 183, 0.2);
        }
        
        .benefit-icon {
            font-size: 1.5rem;
            flex-shrink: 0;
        }
        
        .benefit-item strong {
            display: block;
            color: #00FFB7;
            margin-bottom: 5px;
        }
        
        .benefit-item p {
            margin: 0;
            font-size: 0.9rem;
            opacity: 0.8;
        }
        
        .pricing-section {
            margin-bottom: 30px;
        }
        
        .price-card {
            background: rgba(0, 255, 183, 0.1);
            border: 2px solid rgba(0, 255, 183, 0.3);
            border-radius: 15px;
            padding: 30px 25px;
            text-align: center;
            position: relative;
        }
        
        .price-badge {
            position: absolute;
            top: -10px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #00FFB7 0%, #00D4FF 100%);
            color: #1a1a2e;
            padding: 5px 20px;
            border-radius: 15px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .price {
            display: flex;
            align-items: flex-end;
            justify-content: center;
            gap: 5px;
            margin: 20px 0;
        }
        
        .currency {
            font-size: 1.5rem;
            opacity: 0.8;
        }
        
        .amount {
            font-size: 3rem;
            font-weight: bold;
            color: #00FFB7;
        }
        
        .period {
            font-size: 1rem;
            opacity: 0.8;
            margin-bottom: 8px;
        }
        
        .price-features {
            list-style: none;
            padding: 0;
            margin: 20px 0 0;
        }
        
        .price-features li {
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .price-features li:last-child {
            border-bottom: none;
        }
        
        .payment-methods {
            margin-bottom: 30px;
        }
        
        .payment-options {
            display: grid;
            gap: 15px;
            margin-top: 20px;
        }
        
        .payment-option {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .payment-option:hover {
            background: rgba(0, 255, 183, 0.1);
            border-color: rgba(0, 255, 183, 0.3);
            transform: translateX(5px);
        }
        
        .payment-icon {
            font-size: 1.5rem;
        }
        
        .security-info {
            text-align: center;
            opacity: 0.8;
            font-size: 0.9rem;
        }
        
        .security-info p {
            margin: 10px 0;
        }
        
        .security-icon {
            margin-right: 8px;
        }
        
        /* Processing Modal */
        .processing-content {
            text-align: center;
        }
        
        .processing-animation {
            margin: 30px 0;
        }
        
        .spinner {
            width: 60px;
            height: 60px;
            border: 4px solid rgba(0, 255, 183, 0.3);
            border-top: 4px solid #00FFB7;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .processing-steps {
            margin-top: 30px;
            text-align: left;
        }
        
        .step {
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px 0;
            opacity: 0.5;
        }
        
        .step.completed {
            opacity: 1;
            color: #00FFB7;
        }
        
        .step.processing {
            opacity: 1;
            color: #FFB700;
        }
        
        .step-icon {
            width: 24px;
            text-align: center;
        }
        
        /* Success Modal */
        .success-content {
            text-align: center;
        }
        
        .success-animation {
            position: relative;
            margin: 30px 0;
        }
        
        .success-icon {
            font-size: 4rem;
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-20px); }
            60% { transform: translateY(-10px); }
        }
        
        .success-benefits {
            background: rgba(0, 255, 183, 0.1);
            padding: 25px;
            border-radius: 15px;
            margin: 30px 0;
            border: 2px solid rgba(0, 255, 183, 0.3);
        }
        
        .success-list {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        
        .success-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(0, 255, 183, 0.2);
        }
        
        .telegram-access {
            margin-top: 30px;
            padding: 25px;
            background: rgba(0, 212, 255, 0.1);
            border-radius: 15px;
            border: 2px solid rgba(0, 212, 255, 0.3);
        }
        
        .btn-telegram {
            background: linear-gradient(135deg, #00D4FF 0%, #6B7AFF 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1rem;
            font-weight: bold;
            cursor: pointer;
            margin-top: 15px;
            transition: all 0.3s ease;
        }
        
        .btn-telegram:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4);
        }
        
        /* Upgrade Reminder */
        .upgrade-reminder {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #FFB700 0%, #FF6B6B 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
            z-index: 9999;
            max-width: 350px;
            animation: slideInRight 0.5s ease;
        }
        
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .reminder-content {
            position: relative;
        }
        
        .reminder-icon {
            font-size: 2rem;
            margin-bottom: 10px;
        }
        
        .btn-upgrade {
            background: white;
            color: #FFB700;
            border: none;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: bold;
            cursor: pointer;
            margin-top: 15px;
            transition: all 0.3s ease;
        }
        
        .btn-upgrade:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        .btn-close {
            position: absolute;
            top: -5px;
            right: 0;
            background: none;
            border: none;
            color: white;
            font-size: 20px;
            cursor: pointer;
            width: 30px;
            height: 30px;
        }
        
        /* Confetti */
        @keyframes confetti-fall {
            0% {
                transform: translateY(-100vh) rotate(0deg);
                opacity: 1;
            }
            100% {
                transform: translateY(100vh) rotate(720deg);
                opacity: 0;
            }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .modal-content {
                margin: 10px;
                max-width: calc(100vw - 20px);
            }
            
            .benefits-grid {
                grid-template-columns: 1fr;
            }
            
            .feature-highlights {
                grid-template-columns: 1fr;
            }
            
            .success-list {
                grid-template-columns: 1fr;
            }
            
            .upgrade-reminder {
                top: 10px;
                right: 10px;
                left: 10px;
                max-width: none;
            }
        }
    `;
    
    document.head.appendChild(style);
}

// Interceptar análisis
function interceptAnalysis() {
    if (!canAnalyze()) {
        showPaymentModal();
        return false;
    }
    
    return consumeAnalysis();
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    addPaymentStyles();
    initializePaymentSystem();
});

// Exportar funciones para uso global
window.paymentSystem = {
    canAnalyze,
    consumeAnalysis,
    interceptAnalysis,
    showPaymentModal,
    updateAnalysisCounter,
    userState
};