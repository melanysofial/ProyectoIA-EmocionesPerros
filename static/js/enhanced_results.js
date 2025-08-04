// Sistema mejorado de visualización de resultados con gráficos y estadísticas avanzadas

// Configuración de colores por emoción (tema futurista)
const EMOTION_CONFIG = {
    happy: {
        color: '#00FFB7',
        gradient: 'linear-gradient(135deg, #00FFB7 0%, #00D4FF 100%)',
        icon: '😊',
        description: 'Tu perro está feliz y contento',
        tips: [
            'Continúa con las actividades que lo hacen feliz',
            'Es un buen momento para jugar y entrenar',
            'Refuerza este comportamiento positivo'
        ]
    },
    sad: {
        color: '#6B7AFF',
        gradient: 'linear-gradient(135deg, #6B7AFF 0%, #4B5BFF 100%)',
        icon: '😢',
        description: 'Tu perro muestra señales de tristeza',
        tips: [
            'Dedícale más tiempo y atención',
            'Verifica si tiene alguna molestia física',
            'Considera actividades que lo animen'
        ]
    },
    angry: {
        color: '#FF6B6B',
        gradient: 'linear-gradient(135deg, #FF6B6B 0%, #FF4757 100%)',
        icon: '😠',
        description: 'Tu perro está molesto o estresado',
        tips: [
            'Identifica y elimina la fuente de estrés',
            'Dale espacio para calmarse',
            'Evita confrontaciones directas'
        ]
    },
    relaxed: {
        color: '#B4FF6B',
        gradient: 'linear-gradient(135deg, #B4FF6B 0%, #6BFF9F 100%)',
        icon: '😌',
        description: 'Tu perro está relajado y tranquilo',
        tips: [
            'Mantén el ambiente tranquilo',
            'Es ideal para descanso',
            'Perfecto estado de bienestar'
        ]
    }
};

// Función para crear gráfico circular (donut chart)
function createDonutChart(containerId, data) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const width = 300;
    const height = 300;
    const radius = Math.min(width, height) / 2;
    const innerRadius = radius * 0.6;

    // Limpiar contenedor
    container.innerHTML = '';

    // Crear SVG
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('width', width);
    svg.setAttribute('height', height);
    svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    svg.style.width = '100%';
    svg.style.height = 'auto';

    // Calcular ángulos
    const total = Object.values(data).reduce((sum, val) => sum + val, 0);
    let currentAngle = -90; // Empezar desde arriba

    // Crear grupo centrado
    const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
    g.setAttribute('transform', `translate(${width/2}, ${height/2})`);

    // Crear segmentos
    Object.entries(data).forEach(([emotion, count]) => {
        if (count === 0) return;

        const percentage = count / total;
        const angle = percentage * 360;
        const endAngle = currentAngle + angle;

        // Crear path del segmento
        const path = createArcPath(0, 0, radius, innerRadius, currentAngle, endAngle);
        const segment = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        segment.setAttribute('d', path);
        segment.setAttribute('fill', EMOTION_CONFIG[emotion].color);
        segment.setAttribute('stroke', 'rgba(0,0,0,0.3)');
        segment.setAttribute('stroke-width', '2');
        segment.style.filter = 'drop-shadow(0 4px 8px rgba(0,0,0,0.3))';
        segment.style.cursor = 'pointer';
        segment.style.transition = 'all 0.3s ease';

        // Efecto hover
        segment.addEventListener('mouseenter', () => {
            segment.style.transform = 'scale(1.05)';
            segment.style.filter = 'drop-shadow(0 6px 12px rgba(0,0,0,0.5))';
        });

        segment.addEventListener('mouseleave', () => {
            segment.style.transform = 'scale(1)';
            segment.style.filter = 'drop-shadow(0 4px 8px rgba(0,0,0,0.3))';
        });

        g.appendChild(segment);

        // Agregar etiqueta si el porcentaje es significativo
        if (percentage > 0.05) {
            const labelAngle = (currentAngle + endAngle) / 2;
            const labelRadius = (radius + innerRadius) / 2;
            const x = Math.cos(labelAngle * Math.PI / 180) * labelRadius;
            const y = Math.sin(labelAngle * Math.PI / 180) * labelRadius;

            const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
            text.setAttribute('x', x);
            text.setAttribute('y', y);
            text.setAttribute('text-anchor', 'middle');
            text.setAttribute('dominant-baseline', 'middle');
            text.setAttribute('fill', 'white');
            text.setAttribute('font-size', '14');
            text.setAttribute('font-weight', 'bold');
            text.textContent = `${Math.round(percentage * 100)}%`;
            g.appendChild(text);
        }

        currentAngle = endAngle;
    });

    // Agregar texto central
    const centerText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    centerText.setAttribute('x', 0);
    centerText.setAttribute('y', -10);
    centerText.setAttribute('text-anchor', 'middle');
    centerText.setAttribute('fill', 'white');
    centerText.setAttribute('font-size', '24');
    centerText.setAttribute('font-weight', 'bold');
    centerText.textContent = total;

    const centerLabel = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    centerLabel.setAttribute('x', 0);
    centerLabel.setAttribute('y', 15);
    centerLabel.setAttribute('text-anchor', 'middle');
    centerLabel.setAttribute('fill', '#888');
    centerLabel.setAttribute('font-size', '14');
    centerLabel.textContent = 'Análisis';

    g.appendChild(centerText);
    g.appendChild(centerLabel);
    svg.appendChild(g);
    container.appendChild(svg);
}

// Función auxiliar para crear path de arco
function createArcPath(cx, cy, outerRadius, innerRadius, startAngle, endAngle) {
    const start = polarToCartesian(cx, cy, outerRadius, endAngle);
    const end = polarToCartesian(cx, cy, outerRadius, startAngle);
    const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";

    const outerArc = `M ${start.x} ${start.y} A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
    
    const innerStart = polarToCartesian(cx, cy, innerRadius, endAngle);
    const innerEnd = polarToCartesian(cx, cy, innerRadius, startAngle);
    const innerArc = `L ${innerEnd.x} ${innerEnd.y} A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 1 ${innerStart.x} ${innerStart.y}`;

    return `${outerArc} ${innerArc} Z`;
}

function polarToCartesian(centerX, centerY, radius, angleInDegrees) {
    const angleInRadians = (angleInDegrees - 90) * Math.PI / 180.0;
    return {
        x: centerX + (radius * Math.cos(angleInRadians)),
        y: centerY + (radius * Math.sin(angleInRadians))
    };
}

// Función para crear timeline de emociones
function createEmotionTimeline(containerId, emotions) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';
    
    const timeline = document.createElement('div');
    timeline.className = 'emotion-timeline';
    timeline.style.cssText = `
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 15px;
        background: rgba(255,255,255,0.05);
        border-radius: 15px;
        overflow-x: auto;
        min-height: 80px;
    `;

    emotions.forEach((emotion, index) => {
        const block = document.createElement('div');
        block.style.cssText = `
            min-width: 40px;
            height: 40px;
            background: ${EMOTION_CONFIG[emotion].gradient};
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            position: relative;
        `;
        
        block.innerHTML = EMOTION_CONFIG[emotion].icon;
        block.title = `Frame ${index + 1}: ${emotion}`;

        // Efecto hover
        block.addEventListener('mouseenter', () => {
            block.style.transform = 'scale(1.2) translateY(-5px)';
            block.style.zIndex = '10';
        });

        block.addEventListener('mouseleave', () => {
            block.style.transform = 'scale(1) translateY(0)';
            block.style.zIndex = '1';
        });

        timeline.appendChild(block);
    });

    container.appendChild(timeline);
}

// Función principal para mostrar resultados mejorados
function displayEnhancedResults(data) {
    const resultsDiv = document.getElementById('analysisResults');
    if (!resultsDiv) return;

    // Limpiar resultados anteriores
    resultsDiv.innerHTML = '';
    resultsDiv.style.cssText = `
        display: grid;
        gap: 2rem;
        padding: 2rem;
        animation: fadeIn 0.5s ease;
    `;

    // 1. Header con emoción dominante
    const header = document.createElement('div');
    header.style.cssText = `
        text-align: center;
        padding: 2rem;
        background: ${EMOTION_CONFIG[data.dominant_emotion].gradient};
        border-radius: 20px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    `;
    
    header.innerHTML = `
        <div style="font-size: 5rem; margin-bottom: 1rem;">
            ${EMOTION_CONFIG[data.dominant_emotion].icon}
        </div>
        <h2 style="font-size: 2.5rem; margin-bottom: 1rem; color: white; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">
            Emoción Dominante: ${data.dominant_emotion.toUpperCase()}
        </h2>
        <p style="font-size: 1.3rem; opacity: 0.9; color: white;">
            ${EMOTION_CONFIG[data.dominant_emotion].description}
        </p>
        <div style="margin-top: 1.5rem;">
            <span style="background: rgba(0,0,0,0.3); padding: 0.5rem 1.5rem; border-radius: 20px; font-size: 1.2rem;">
                Confianza: ${(data.confidence_avg * 100).toFixed(1)}%
            </span>
        </div>
    `;
    resultsDiv.appendChild(header);

    // 2. Grid de estadísticas
    const statsGrid = document.createElement('div');
    statsGrid.style.cssText = `
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
    `;

    // 2.1 Gráfico circular
    const chartCard = createCard('Distribución de Emociones', `
        <div id="emotionDonutChart" style="display: flex; justify-content: center; padding: 2rem;"></div>
        <div id="legendContainer" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem;"></div>
    `);
    statsGrid.appendChild(chartCard);

    // 2.2 Estadísticas detalladas
    const statsCard = createCard('Estadísticas del Análisis', `
        <div style="display: grid; gap: 1rem;">
            <div class="stat-item">
                <i class="fas fa-video" style="color: var(--primary); margin-right: 0.5rem;"></i>
                <span>Frames analizados:</span>
                <strong>${data.total_frames || data.total_emotions}</strong>
            </div>
            <div class="stat-item">
                <i class="fas fa-dog" style="color: var(--secondary); margin-right: 0.5rem;"></i>
                <span>Detecciones de perro:</span>
                <strong>${data.total_detections || data.total_emotions}</strong>
            </div>
            <div class="stat-item">
                <i class="fas fa-chart-line" style="color: var(--gold); margin-right: 0.5rem;"></i>
                <span>Confianza promedio:</span>
                <strong>${(data.confidence_avg * 100).toFixed(1)}%</strong>
            </div>
            <div class="stat-item">
                <i class="fas fa-clock" style="color: #00FFB7; margin-right: 0.5rem;"></i>
                <span>Tiempo de análisis:</span>
                <strong>${data.processing_time || 'N/A'}</strong>
            </div>
        </div>
    `);
    statsGrid.appendChild(statsCard);

    resultsDiv.appendChild(statsGrid);

    // 3. Timeline de emociones (si hay datos)
    if (data.emotion_timeline && data.emotion_timeline.length > 0) {
        const timelineCard = createCard('Timeline de Emociones', `
            <p style="margin-bottom: 1rem; opacity: 0.8;">Evolución emocional a lo largo del video:</p>
            <div id="emotionTimeline"></div>
        `);
        resultsDiv.appendChild(timelineCard);
    }

    // 4. Barras de progreso por emoción
    const barsCard = createCard('Análisis Detallado por Emoción', '');
    const barsContainer = document.createElement('div');
    barsContainer.style.cssText = 'display: grid; gap: 1.5rem;';

    Object.entries(data.emotion_distribution).forEach(([emotion, count]) => {
        const percentage = (count / data.total_emotions * 100).toFixed(1);
        const emotionBar = document.createElement('div');
        emotionBar.innerHTML = `
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="font-weight: bold; color: ${EMOTION_CONFIG[emotion].color};">
                    ${EMOTION_CONFIG[emotion].icon} ${emotion.charAt(0).toUpperCase() + emotion.slice(1)}
                </span>
                <span style="font-weight: bold;">${percentage}%</span>
            </div>
            <div style="background: rgba(255,255,255,0.1); border-radius: 10px; overflow: hidden; height: 30px;">
                <div style="
                    width: ${percentage}%;
                    height: 100%;
                    background: ${EMOTION_CONFIG[emotion].gradient};
                    border-radius: 10px;
                    transition: width 1s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                ">
                    ${count} detecciones
                </div>
            </div>
        `;
        barsContainer.appendChild(emotionBar);
    });
    
    barsCard.querySelector('.card-content').appendChild(barsContainer);
    resultsDiv.appendChild(barsCard);

    // 5. Recomendaciones personalizadas
    const recommendationsCard = createCard('💡 Recomendaciones Personalizadas', '');
    const recsContent = document.createElement('div');
    
    // Recomendaciones basadas en la emoción dominante
    const tips = EMOTION_CONFIG[data.dominant_emotion].tips;
    recsContent.innerHTML = `
        <div style="background: ${EMOTION_CONFIG[data.dominant_emotion].gradient}; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
            <h4 style="margin-bottom: 0.5rem;">Basado en el estado emocional de tu perro:</h4>
        </div>
        <ul style="list-style: none; padding: 0;">
            ${tips.map(tip => `
                <li style="margin-bottom: 1rem; padding-left: 2rem; position: relative;">
                    <i class="fas fa-check-circle" style="position: absolute; left: 0; top: 0.2rem; color: var(--primary);"></i>
                    ${tip}
                </li>
            `).join('')}
        </ul>
    `;

    // Si hay emociones negativas predominantes
    if (data.emotion_distribution.angry > data.total_emotions * 0.3 || 
        data.emotion_distribution.sad > data.total_emotions * 0.3) {
        recsContent.innerHTML += `
            <div style="background: rgba(255,107,107,0.2); border: 2px solid #FF6B6B; padding: 1rem; border-radius: 10px; margin-top: 1rem;">
                <i class="fas fa-exclamation-triangle" style="color: #FF6B6B; margin-right: 0.5rem;"></i>
                <strong>Atención:</strong> Se detectaron niveles altos de emociones negativas. 
                Considera consultar con un veterinario o especialista en comportamiento canino.
            </div>
        `;
    }

    recommendationsCard.querySelector('.card-content').appendChild(recsContent);
    resultsDiv.appendChild(recommendationsCard);

    // 6. Botón para descargar reporte
    const actionsCard = document.createElement('div');
    actionsCard.style.cssText = `
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin-top: 2rem;
    `;
    
    actionsCard.innerHTML = `
        <button class="cta-button" onclick="downloadReport()" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            border-radius: 50px;
            border: none;
            font-size: 1.1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
        ">
            <i class="fas fa-download"></i>
            Descargar Reporte Completo
        </button>
        <button class="cta-button" onclick="shareResults()" style="
            background: linear-gradient(135deg, #00FFB7 0%, #00D4FF 100%);
            color: #0a0e27;
            padding: 1rem 2rem;
            border-radius: 50px;
            border: none;
            font-size: 1.1rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            transition: all 0.3s ease;
        ">
            <i class="fas fa-share-alt"></i>
            Compartir Resultados
        </button>
    `;
    
    resultsDiv.appendChild(actionsCard);

    // Renderizar gráficos y animaciones
    setTimeout(() => {
        createDonutChart('emotionDonutChart', data.emotion_distribution);
        
        // Crear leyenda
        const legendContainer = document.getElementById('legendContainer');
        if (legendContainer) {
            Object.entries(data.emotion_distribution).forEach(([emotion, count]) => {
                const percentage = (count / data.total_emotions * 100).toFixed(1);
                const legendItem = document.createElement('div');
                legendItem.style.cssText = 'display: flex; align-items: center; gap: 0.5rem;';
                legendItem.innerHTML = `
                    <div style="width: 20px; height: 20px; background: ${EMOTION_CONFIG[emotion].color}; border-radius: 4px;"></div>
                    <span>${emotion}: ${percentage}%</span>
                `;
                legendContainer.appendChild(legendItem);
            });
        }

        if (data.emotion_timeline) {
            createEmotionTimeline('emotionTimeline', data.emotion_timeline);
        }
    }, 100);
}

// Función auxiliar para crear cards
function createCard(title, content) {
    const card = document.createElement('div');
    card.className = 'glass-card';
    card.style.cssText = `
        background: var(--glass);
        backdrop-filter: blur(10px);
        border: 1px solid var(--glass-border);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    `;
    
    card.innerHTML = `
        <h3 style="margin-bottom: 1.5rem; color: var(--primary); display: flex; align-items: center; gap: 0.5rem;">
            ${title}
        </h3>
        <div class="card-content">
            ${content}
        </div>
    `;
    
    return card;
}

// Función para descargar reporte
function downloadReport() {
    // Aquí iría la lógica para generar y descargar un PDF
    alert('Función de descarga de reporte en desarrollo. Próximamente disponible!');
}

// Función para compartir resultados
function shareResults() {
    // Aquí iría la lógica para compartir
    alert('Función de compartir en desarrollo. Próximamente disponible!');
}

// Estilos CSS adicionales
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .stat-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.8rem;
        background: rgba(255,255,255,0.05);
        border-radius: 10px;
        transition: all 0.3s ease;
    }

    .stat-item:hover {
        background: rgba(255,255,255,0.1);
        transform: translateX(5px);
    }

    .emotion-timeline::-webkit-scrollbar {
        height: 8px;
    }

    .emotion-timeline::-webkit-scrollbar-track {
        background: rgba(255,255,255,0.1);
        border-radius: 4px;
    }

    .emotion-timeline::-webkit-scrollbar-thumb {
        background: var(--primary);
        border-radius: 4px;
    }

    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
    }
`;
document.head.appendChild(style);

// Exportar función para uso global
window.displayEnhancedResults = displayEnhancedResults;