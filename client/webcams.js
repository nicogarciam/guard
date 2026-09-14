document.addEventListener('DOMContentLoaded', () => {
    // Si abrimos por HTTPS (Cloudflare), usamos rutas relativas para evitar el Mixed Content.
    // Si estamos en local (HTTP), le pegamos al puerto 1984 directo.
    const isProd = window.location.protocol === 'https:';
    const host = (window.location.hostname === '' || window.location.hostname === 'localhost') ? '127.0.0.1' : window.location.hostname;
    const baseUrl = isProd ? '' : `http://${host}:1984`;
    
    const statusBadge = document.getElementById('connection-status');
    const countBadge = document.getElementById('camera-count');
    const grid = document.getElementById('cameras-grid');

    let currentStreams = [];

    async function init() {
        try {
            // Hacemos fetch a la API de go2rtc para obtener los streams configurados
            const response = await fetch(`${baseUrl}/api/streams`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            const data = await response.json();
            const streams = Object.keys(data).sort();
            
            // Actualizar UI
            statusBadge.textContent = 'Conectado';
            statusBadge.classList.remove('connecting', 'error');
            statusBadge.classList.add('connected');
            
            countBadge.textContent = `${streams.length} Cámara${streams.length !== 1 ? 's' : ''}`;
            
            if (JSON.stringify(currentStreams) !== JSON.stringify(streams)) {
                renderCameras(streams);
                currentStreams = streams;
            }
            
        } catch (error) {
            console.error('Error conectando a go2rtc:', error);
            statusBadge.textContent = 'Error de Conexión';
            statusBadge.classList.remove('connecting', 'connected');
            statusBadge.classList.add('error');
            currentStreams = []; // Reset para forzar re-render cuando vuelva la conexión
            
            grid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; color: #ff453a; padding: 2rem;">
                    <h3>No se pudo conectar con el servidor de cámaras.</h3>
                    <p>Verificá que el servicio 'guard-webcams' esté corriendo y go2rtc esté activo en el puerto 1984.</p>
                </div>
            `;
        }
    }

    function renderCameras(streams) {
        grid.innerHTML = '';
        
        streams.forEach(streamName => {
            // Crear tarjeta de cámara
            const card = document.createElement('div');
            card.className = 'camera-card';
            
            // Header de la tarjeta
            const header = document.createElement('div');
            header.className = 'camera-header';
            
            const title = document.createElement('div');
            title.className = 'camera-title';
            // Formatear nombre (ej: camara_frente -> Camara Frente)
            title.textContent = streamName.replace(/_/g, ' ');
            
            // Controles del header (Live + Expandir)
            const controls = document.createElement('div');
            controls.className = 'header-controls';
            
            const liveIndicator = document.createElement('div');
            liveIndicator.innerHTML = '<span style="color: #ff453a; font-size: 0.65rem; margin-right: 6px;">● LIVE</span>';
            
            const expandBtn = document.createElement('button');
            expandBtn.className = 'btn-expand';
            expandBtn.textContent = '🔍 Ampliar';
            
            // Lógica de expandir
            expandBtn.onclick = () => {
                const isExpanded = card.classList.contains('expanded');
                if (isExpanded) {
                    card.classList.remove('expanded');
                    expandBtn.textContent = '🔍 Ampliar';
                    document.body.style.overflow = ''; // Restaurar scroll
                } else {
                    card.classList.add('expanded');
                    expandBtn.textContent = '✖ Reducir';
                    document.body.style.overflow = 'hidden'; // Evitar scroll de fondo
                }
            };
            
            controls.appendChild(liveIndicator);
            controls.appendChild(expandBtn);
            
            header.appendChild(title);
            header.appendChild(controls);
            
            // Contenedor del video
            const feed = document.createElement('div');
            feed.className = 'camera-feed';
            
            // Spinner de carga (se oculta cuando carga el iframe)
            // Al usar stream.html, si hay un micro-corte y hace fallback, el JS interno
            // de go2rtc puede perder el parámetro de mute y habilitar el audio por error.
            // Para blindar esto al 100%, volamos el iframe y usamos un tag <video> nativo nuestro,
            // pegándole directamente al endpoint de MSE (stream.mp4).
            const spinner = document.createElement('div');
            spinner.className = 'loading-spinner';
            
            const video = document.createElement('video');
            video.src = `${baseUrl}/api/stream.mp4?src=${streamName}`;
            video.autoplay = true;
            video.muted = true; // FIJO en el DOM, es físicamente imposible que se desmutee solo
            video.controls = false;
            video.style.width = '100%';
            video.style.height = '100%';
            video.style.objectFit = 'contain';
            video.style.background = '#000';
            video.style.pointerEvents = 'none'; // Sin interacción
            
            video.onplaying = () => spinner.style.display = 'none';
            video.onwaiting = () => spinner.style.display = 'block';
            video.onstalled = () => spinner.style.display = 'block';
            
            const watermark = document.createElement('a');
            watermark.className = 'camera-watermark';
            watermark.href = 'https://www.instagram.com/bahiacreek.elprincipito/?hl=es';
            watermark.target = '_blank';
            watermark.innerHTML = '@bahiacreek.elprincipito';
            
            feed.appendChild(spinner);
            feed.appendChild(video);
            feed.appendChild(watermark);
            
            card.appendChild(header);
            card.appendChild(feed);
            
            grid.appendChild(card);
        });
    }

    // Iniciar
    init();
    
    // Auto-recargar la lista cada 30 segundos por si agregan cámaras
    setInterval(init, 30000);
});
