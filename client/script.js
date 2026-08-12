// --- CONFIGURACIÓN INICIAL & ESTADO ---
let client = null;
let logs = JSON.parse(localStorage.getItem('guard_mqtt_logs') || '[]');

// Generar un ID de cliente web único al azar
document.getElementById('client-id').value += Math.random().toString(36).substring(2, 8);

// --- REFERENCIAS A ELEMENTOS DEL DOM ---
const btnConnect = document.getElementById('btn-connect');
const btnPublish = document.getElementById('btn-publish');
const btnOpenGate = document.getElementById('btn-open-gate');
const btnClear = document.getElementById('btn-clear');
const connectionStatus = document.getElementById('connection-status');
const statusText = document.getElementById('status-text');

const hostInput = document.getElementById('broker-host');
const portInput = document.getElementById('broker-port');
const pathInput = document.getElementById('broker-path');
const userInput = document.getElementById('broker-user');
const passInput = document.getElementById('broker-pass');
const clientIdInput = document.getElementById('client-id');

const publishTopic = document.getElementById('publish-topic');
const publishPayload = document.getElementById('publish-payload');

const filterSearch = document.getElementById('filter-search');
const filterTopicButtons = document.querySelectorAll('.topic-filter-btn');

const messagesUl = document.getElementById('messages-ul');
const noMessagesView = document.getElementById('no-messages-view');
const messageCount = document.getElementById('message-count');

// Carga inicial del historial
renderLogs();

// --- CONEXIÓN MQTT ---
btnConnect.addEventListener('click', () => {
    if (client && client.connected) {
        // Desconectar
        client.end(false, () => {
            updateStatus('disconnected', 'Desconectado');
            btnConnect.innerHTML = `
                        <svg style="width:1.15rem;height:1.15rem;fill:currentColor;" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.12 0 2.07-.76 2.36-1.81 1.76 1.48 2.97 3.61 3.18 6.02.04.59-.11 1.17-.64 1.72z"/></svg>
                        Conectar
                    `;
            toggleInputs(false);
        });
        return;
    }

    // Conectar
    updateStatus('connecting', 'Conectando...');
    toggleInputs(true);

    const host = hostInput.value.trim();
    const port = portInput.value.trim();
    const path = pathInput.value.trim();
    const username = userInput.value.trim();
    const password = passInput.value.trim();
    const clientId = clientIdInput.value.trim();

    const url = `wss://${host}:${port}${path}`;
    console.log(`Intentando conectar a: ${url}`);

    const options = {
        clientId: clientId,
        username: username,
        password: password,
        connectTimeout: 7000,
        reconnectPeriod: 4000,
        keepalive: 60,
        rejectUnauthorized: false
    };

    try {
        client = mqtt.connect(url, options);

        client.on('connect', () => {
            console.log('¡Conexión MQTT exitosa!');
            updateStatus('connected', 'Conectado');
            btnConnect.innerHTML = `
                        <svg style="width:1.15rem;height:1.15rem;fill:currentColor;" viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                        Desconectar
                    `;

            // Suscribirse a los tópicos definidos en config.py
            client.subscribe('mi_porton/comando');
            client.subscribe('mi_porton/estado');
            client.subscribe('mi_porton/evento');
        });

        client.on('message', (topic, message) => {
            const rawPayload = message.toString();
            console.log(`Mensaje recibido [${topic}]: ${rawPayload}`);
            saveLog(topic, rawPayload, 'IN');
        });

        client.on('error', (err) => {
            console.error('Error MQTT:', err);
            updateStatus('disconnected', 'Error de red');
        });

        client.on('close', () => {
            console.log('Conexión cerrada por el Broker');
            updateStatus('disconnected', 'Desconectado');
        });
    } catch (err) {
        console.error('Excepción al conectar:', err);
        updateStatus('disconnected', 'Error');
    }
});

// --- ENVIAR COMANDOS ---
btnOpenGate.addEventListener('click', () => {
    if (!client || !client.connected) return;

    const payload = {
        token: "mi_secreto_super_seguro_123",
        accion: "ABRIR",
        timestamp: new Date().toISOString()
    };

    const payloadStr = JSON.stringify(payload);
    client.publish('mi_porton/comando', payloadStr, { qos: 0 });
    saveLog('mi_porton/comando', payloadStr, 'OUT');

    // Efecto visual rápido en el botón
    const originalText = btnOpenGate.innerHTML;
    btnOpenGate.innerHTML = "🔓 ¡Comando ABRIR Enviado!";
    btnOpenGate.style.background = "rgba(0, 242, 167, 0.25)";
    setTimeout(() => {
        btnOpenGate.innerHTML = originalText;
        btnOpenGate.style.background = "";
    }, 2000);
});

// --- ENVIAR MENSAJE PERSONALIZADO ---
btnPublish.addEventListener('click', () => {
    if (!client || !client.connected) return;

    const topic = publishTopic.value;
    let payloadText = publishPayload.value;

    // Rellenar timestamp automático si está vacío en el JSON
    try {
        const parsed = JSON.parse(payloadText);
        if (parsed.hasOwnProperty('timestamp') && parsed.timestamp === "") {
            parsed.timestamp = new Date().toISOString();
        }
        payloadText = JSON.stringify(parsed, null, 2);
        publishPayload.value = payloadText;
    } catch (e) {
        // Si no es JSON válido, enviar como texto plano
    }

    client.publish(topic, payloadText, { qos: 0 });
    saveLog(topic, payloadText, 'OUT');
});

// --- CONTROL DE UI ---
function updateStatus(status, text) {
    connectionStatus.className = `status-badge status-${status}`;
    statusText.innerText = text;

    if (status === 'connected') {
        btnPublish.disabled = false;
        btnOpenGate.disabled = false;
    } else {
        btnPublish.disabled = true;
        btnOpenGate.disabled = true;
    }
}

function toggleInputs(disabled) {
    hostInput.disabled = disabled;
    portInput.disabled = disabled;
    pathInput.disabled = disabled;
    userInput.disabled = disabled;
    passInput.disabled = disabled;
    clientIdInput.disabled = disabled;
}

// --- MANEJO DE HISTORIAL Y LOCALSTORAGE ---
function saveLog(topic, payloadRaw, direction) {
    let parsedPayload = payloadRaw;
    let isJson = false;

    try {
        parsedPayload = JSON.parse(payloadRaw);
        isJson = true;
    } catch (e) {
        // No es JSON válido, mantener como cadena
    }

    const newLog = {
        id: Date.now() + Math.random().toString(36).substring(2, 6),
        topic: topic,
        payload: parsedPayload,
        raw: payloadRaw,
        isJson: isJson,
        direction: direction, // 'IN' (recibido), 'OUT' (enviado)
        timestamp: new Date().toISOString()
    };

    logs.unshift(newLog); // Añadir al inicio para mostrarlo primero

    // Limitar a 400 registros para evitar agotar el LocalStorage
    if (logs.length > 400) {
        logs = logs.slice(0, 400);
    }

    localStorage.setItem('guard_mqtt_logs', JSON.stringify(logs));
    renderLogs();
}

btnClear.addEventListener('click', () => {
    if (confirm('¿Estás seguro de que quieres vaciar todo el historial guardado en LocalStorage?')) {
        logs = [];
        localStorage.removeItem('guard_mqtt_logs');
        renderLogs();
    }
});

// Eventos de filtro
filterTopicButtons.forEach(btn => {
    btn.addEventListener('click', () => {
        btn.classList.toggle('active');
        renderLogs();
    });
});
filterSearch.addEventListener('input', renderLogs);

function renderLogs() {
    // Limpiar la lista actual (excepto la vista por defecto de 'sin mensajes')
    const items = messagesUl.querySelectorAll('.message-item');
    items.forEach(el => el.remove());

    const activeTopics = Array.from(document.querySelectorAll('.topic-filter-btn.active')).map(btn => btn.dataset.topic);
    const searchVal = filterSearch.value.trim().toLowerCase();

    // Filtrar
    const filteredLogs = logs.filter(log => {
        const matchesTopic = activeTopics.includes(log.topic);

        let matchesSearch = true;
        if (searchVal) {
            const rawStr = log.raw.toLowerCase();
            const topicStr = log.topic.toLowerCase();
            const directionStr = log.direction === 'IN' ? 'recibido entry' : 'enviado exit';

            // Buscar en el texto bruto, tópico o propiedades de evento específicas
            let eventStr = '';
            if (log.isJson && log.payload.event) {
                eventStr = log.payload.event.toLowerCase();
            }

            matchesSearch = rawStr.includes(searchVal) ||
                topicStr.includes(searchVal) ||
                eventStr.includes(searchVal) ||
                directionStr.includes(searchVal);
        }

        return matchesTopic && matchesSearch;
    });

    // Actualizar contador
    messageCount.innerText = `${filteredLogs.length} mensajes`;

    if (filteredLogs.length === 0) {
        noMessagesView.style.display = 'flex';
        return;
    }

    noMessagesView.style.display = 'none';

    filteredLogs.forEach(log => {
        const li = document.createElement('li');
        li.className = 'message-item';
        li.dataset.id = log.id;

        const timeFormatted = new Date(log.timestamp).toLocaleTimeString();
        const directionBadge = log.direction === 'IN'
            ? `<span class="badge badge-direction-in">← Recibido</span>`
            : `<span class="badge badge-direction-out">→ Enviado</span>`;

        let messageBodyHtml = '';
        let customBadges = '';
        let plateHeaderHtml = '';

        if (log.isJson) {
            const data = log.payload;
            let plate = '';
            if (data.event === 'PLATE_VALIDATION') {
                plate = data.plate;
            } else if (data.event === 'LPR_DETECTION') {
                plate = (data.result && data.result.plate) || '';
            }
            if (plate) {
                const isMercosur = /^[A-Z]{2}\d{3}[A-Z]{2}$/i.test(plate);
                const plateClass = isMercosur ? 'plate-badge plate-badge-mercosur' : 'plate-badge';
                plateHeaderHtml = `<span class="${plateClass}" >
                ${escapeHtml(plate.toUpperCase())}</span>`;
            }
            const cleanDsc = data.dsc ? cleanMethodName(data.dsc) : '';

            if (data.event) {
                customBadges += `<span class="badge badge-event">${data.event}</span>`;
            }

            // 1. Tópico estado (mi_porton/estado)
            if (log.topic === 'mi_porton/estado') {
                const estado = data.estado || 'DESCONOCIDO';
                const isOnline = estado === 'EN_LINEA';
                const isOffline = estado === 'OFFLINE';

                let estadoClass = 'state-online';
                if (isOffline) estadoClass = 'state-offline';
                else if (estado !== 'EN_LINEA') estadoClass = 'badge-direction-out';

                customBadges += `<span class="state-badge ${estadoClass}">${estado}</span>`;

                messageBodyHtml = `
                            <div style="display: flex; align-items: center; gap: 0.75rem;">
                                <span style="font-weight: 500; font-size: 0.95rem;">El dispositivo cambió de estado a: <span style="color: #fff; font-weight: 600;">${estado}</span></span>
                            </div>
                        `;
            }
            // 2. Evento PLATE_VALIDATION
            else if (data.event === 'PLATE_VALIDATION') {
                const authorized = data.authorized;
                const plate = data.plate || 'SIN PATENTE';
                const authBadge = authorized
                    ? `<span class="badge badge-authorized">Autorizado</span>`
                    : `<span class="badge badge-unauthorized">Rechazado</span>`;

                customBadges += authBadge;

                // Determinar formato de patente para diseño (Mercosur suele ser AA123AA o similar, 7 caracteres)
                const isMercosur = /^[A-Z]{2}\d{3}[A-Z]{2}$/i.test(plate);
                const plateClass = isMercosur ? 'plate-badge plate-badge-mercosur' : 'plate-badge';

                messageBodyHtml = `
                            <div style="display: flex; flex-direction: column; gap: 0.5rem;">
                                <div style="font-weight: 500; color: var(--text-muted); font-size: 0.9rem;">${escapeHtml(cleanDsc)}</div>
                                <div style="display: flex; align-items: center; gap: 1rem; margin-top: 0.25rem;">
                                    <span class="${plateClass}">${escapeHtml(plate.toUpperCase())}</span>
                                    <span style="font-size: 0.95rem; font-weight: 700; color: ${authorized ? 'var(--success)' : 'var(--danger)'}; letter-spacing: 0.02em;">
                                        ${authorized ? '🔓 ACCESO AUTORIZADO' : '⛔ ACCESO DENEGADO'}
                                    </span>
                                </div>
                            </div>
                        `;
            }
            // 3. Evento LPR_DETECTION
            else if (data.event === 'LPR_DETECTION') {
                const success = data.success;
                const plate = (data.result && data.result.plate) || '';

                let detailsHtml = '';
                if (success && plate) {
                    const isMercosur = /^[A-Z]{2}\d{3}[A-Z]{2}$/i.test(plate);
                    const plateClass = isMercosur ? 'plate-badge plate-badge-mercosur' : 'plate-badge';

                    const vehicle = data.result.vehicle || {};
                    const vType = vehicle.type || 'Desconocido';
                    const vColor = vehicle.color || 'N/A';
                    const vScore = vehicle.score ? `${(vehicle.score * 100).toFixed(1)}%` : 'N/A';

                    detailsHtml = `
                                <div style="display: flex; align-items: center; gap: 1rem; margin-top: 0.25rem; flex-wrap: wrap;">
                                    <span class="${plateClass}">${escapeHtml(plate.toUpperCase())}</span>
                                    <span style="font-size: 0.9rem; font-weight: 500; color: var(--primary);">Patente Detectada</span>
                                </div>
                                <div class="details-grid">
                                    <div class="detail-item">
                                        <span class="detail-label">Vehículo</span>
                                        <span class="detail-value">${escapeHtml(vType)}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Confianza LPR</span>
                                        <span class="detail-value">${escapeHtml(vScore)}</span>
                                    </div>
                                    <div class="detail-item">
                                        <span class="detail-label">Color</span>
                                        <span class="detail-value">${escapeHtml(vColor)}</span>
                                    </div>
                                </div>
                            `;
                } else {
                    detailsHtml = `<div style="color: var(--danger); font-weight: 500; font-size: 0.9rem;">⚠️ No se detectó ninguna patente en la imagen.</div>`;
                }

                messageBodyHtml = `
                            <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                                <div style="font-weight: 500; color: var(--text-muted); font-size: 0.9rem;">${escapeHtml(cleanDsc)}</div>
                                ${detailsHtml}
                            </div>
                        `;
            }
            // 4. Evento LPR_ANALYSIS_TEST_INIT
            else if (data.event === 'LPR_ANALYSIS_TEST_INIT') {
                messageBodyHtml = `
                            <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                                <div style="font-weight: 500; color: var(--text-muted); font-size: 0.9rem;">${escapeHtml(cleanDsc)}</div>
                                <div style="font-size: 0.9rem; color: var(--text-main); font-weight: 500; margin-top: 0.25rem;">
                                    Archivo origen: <span style="font-family: monospace; color: var(--primary); background: rgba(0, 242, 254, 0.08); padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid rgba(0, 242, 254, 0.15);">${escapeHtml(data.source_file || '')}</span>
                                </div>
                            </div>
                        `;
            }
            // 5. Otros JSON
            else {
                const dscVal = cleanDsc || data.accion || 'Mensaje de datos';
                messageBodyHtml = `
                            <div style="font-weight: 500; color: #fff; font-size: 0.95rem;">${escapeHtml(dscVal)}</div>
                            <div style="font-size: 0.85rem; color: var(--text-muted); font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-top: 0.25rem;">
                                ${escapeHtml(JSON.stringify(data))}
                            </div>
                        `;
            }
        } else {
            // Texto plano
            messageBodyHtml = `
                        <div style="font-family: monospace; font-size: 0.85rem; word-break: break-all; color: var(--text-main);">
                            ${escapeHtml(log.raw)}
                        </div>
                    `;
        }

        const prettyJson = log.isJson ? JSON.stringify(log.payload, null, 2) : log.raw;

        li.innerHTML = `
                    <div class="message-top">
                        <div class="row-left">
                            <span class="message-topic">${log.topic}</span>
                        </div>
                        <div>
                            ${customBadges}
                            ${plateHeaderHtml}
                        </div>
                        <div class="row-right">
                            <span>
                                ${directionBadge}
                            </span>
                            <span class="message-time">${timeFormatted}</span>
                        </div>
                    </div>
                    <div class="message-details">
                        <div class="message-body">
                            ${messageBodyHtml}
                        </div>
                        <div style="margin-top: 0.75rem;">
                            <label>Contenido del Mensaje</label>
                            <div class="json-viewer">${escapeHtml(prettyJson)}</div>
                        </div>
                    </div>
                `;

        // Evento para expandir
        li.addEventListener('click', (e) => {
            if (e.target.closest('.json-viewer') || e.target.closest('label') || e.target.closest('button')) {
                return;
            }
            li.classList.toggle('active');
        });

        messagesUl.appendChild(li);
    });
}

// Helpers
function cleanMethodName(text) {
    if (typeof text !== 'string') return text;
    // Limpia "<function nombre_funcion at 0x...>" a "nombre_funcion"
    return text.replace(/<function\s+(\w+)\s+at\s+[a-zA-Z0-9xX]+>/g, '$1');
}

function escapeHtml(text) {
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}