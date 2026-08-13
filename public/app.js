document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const canvas = document.getElementById('view-canvas');
  const ctx = canvas.getContext('2d');
  const placeholder = document.getElementById('video-placeholder');
  const cameraStatus = document.getElementById('camera-status');
  const cameraStatusText = document.getElementById('camera-status-text');
  const fpsCounter = document.getElementById('fps-counter');
  const faceCountVal = document.getElementById('face-count-val');
  const latencyVal = document.getElementById('latency-val');
  const btnSnapshot = document.getElementById('btn-snapshot');
  
  // Modal Elements
  const snapshotModal = document.getElementById('snapshot-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const snapshotImg = document.getElementById('snapshot-img');
  const snapshotDetails = document.getElementById('snapshot-details');
  const downloadLink = document.getElementById('download-link');

  // State
  let frameCount = 0;
  let lastFpsCalcTime = performance.now();
  let ws = null;
  let latestPayload = null;

  // Emotion Emojis Map
  const emotionEmojis = {
    'Happy': '😊',
    'Neutral': '😐',
    'Surprise': '😲',
    'Sad': '😢',
    'Angry': '😡',
    'Fear': '😨',
    'Disgust': '🤢'
  };

  // Adjust canvas size to window screen dimensions
  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  }
  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();

  // Connect WebSocket Stream
  function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/stream`;
    
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket Connected');
      placeholder.style.display = 'none';
      cameraStatus.classList.add('online');
      cameraStatusText.textContent = 'Camera Streaming';
    };

    ws.onmessage = (event) => {
      const tStart = performance.now();
      try {
        const data = JSON.parse(event.data);
        latestPayload = data;

        if (data.image) {
          renderFrame(data.image, data.faces, tStart);
        }

        if (data.is_real_camera) {
          cameraStatusText.textContent = 'Hardware Webcam';
        } else {
          cameraStatusText.textContent = 'Virtual Stream';
        }
      } catch (err) {
        console.error('Frame processing error:', err);
      }
    };

    ws.onclose = () => {
      placeholder.style.display = 'flex';
      cameraStatus.classList.remove('online');
      cameraStatusText.textContent = 'Reconnecting...';
      setTimeout(connectWebSocket, 2000);
    };

    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
      ws.close();
    };
  }

  // Render Video Frame & Draw Face Bounding Boxes with Details at Bottom
  function renderFrame(imgBase64, faces, receiveTime) {
    const img = new Image();
    img.onload = () => {
      const cw = canvas.width;
      const ch = canvas.height;
      
      // Draw background image stretched/scaled to cover screen
      ctx.drawImage(img, 0, 0, cw, ch);

      // Scale factors from original 640x480 frame to full screen canvas
      const scaleX = cw / img.naturalWidth;
      const scaleY = ch / img.naturalHeight;

      // Update Face Count & Latency Metrics
      const count = faces ? faces.length : 0;
      faceCountVal.textContent = count;
      const latency = Math.round(performance.now() - receiveTime);
      latencyVal.textContent = `${latency} ms`;

      // Draw Face Boxes & Details Card attached to the bottom of the box
      if (faces && faces.length > 0) {
        faces.forEach((face) => {
          drawFaceBoxWithDetails(face, scaleX, scaleY);
        });
      }

      // Calculate FPS
      frameCount++;
      const now = performance.now();
      if (now - lastFpsCalcTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / (now - lastFpsCalcTime));
        fpsCounter.textContent = `${fps} FPS`;
        frameCount = 0;
        lastFpsCalcTime = now;
      }
    };
    img.src = imgBase64;
  }

  // Draw Clean Box & Bottom Details Banner
  function drawFaceBoxWithDetails(face, scaleX, scaleY) {
    const origBox = face.box;
    const x = origBox.x * scaleX;
    const y = origBox.y * scaleY;
    const w = origBox.w * scaleX;
    const h = origBox.h * scaleY;

    ctx.save();

    // 1. Draw Clean Rectangle Bounding Box
    const isFemale = face.gender === 'Female';
    const primaryColor = isFemale ? '#ec4899' : '#38bdf8';

    ctx.strokeStyle = primaryColor;
    ctx.lineWidth = 3;
    ctx.shadowColor = primaryColor;
    ctx.shadowBlur = 12;
    ctx.strokeRect(x, y, w, h);

    // Corner Reticle Accents
    const cornerSize = Math.min(w, h) * 0.2;
    ctx.lineWidth = 4;
    
    // Top-Left Corner Accent
    ctx.beginPath();
    ctx.moveTo(x, y + cornerSize); ctx.lineTo(x, y); ctx.lineTo(x + cornerSize, y);
    ctx.stroke();

    // Bottom-Right Corner Accent
    ctx.beginPath();
    ctx.moveTo(x + w - cornerSize, y + h); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w, y + h - cornerSize);
    ctx.stroke();

    // 2. Draw Details Card Attached to the BOTTOM of the Box
    const emoji = emotionEmojis[face.emotion] || '😐';
    const ageText = `Age: ${face.age}`;
    const genderText = `${face.gender}`;
    const emotionText = `${emoji} ${face.emotion} (${face.emotion_confidence || 85}%)`;

    // Card dimensions
    const cardPadding = 10;
    const cardHeight = 54;
    const cardY = y + h + 6; // Placed right at the bottom edge of the box
    const cardWidth = Math.max(w, 200);

    // Keep card within canvas vertical bounds
    const finalCardY = (cardY + cardHeight > canvas.height) ? (y - cardHeight - 6) : cardY;

    // Draw Dark Glass Banner at Bottom
    ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.7)';
    ctx.shadowBlur = 10;
    
    // Rounded Banner Box
    drawRoundedRect(ctx, x, finalCardY, cardWidth, cardHeight, 8);
    ctx.fill();

    // Left Border Indicator Bar
    ctx.fillStyle = primaryColor;
    ctx.fillRect(x, finalCardY, 4, cardHeight);

    // Text Details: Line 1 (Gender & Age)
    ctx.shadowBlur = 0;
    ctx.font = 'bold 15px Inter, sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.fillText(`${genderText} • ${ageText}`, x + cardPadding + 4, finalCardY + 22);

    // Text Details: Line 2 (Emotion & Confidence)
    ctx.font = '500 13px Inter, sans-serif';
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText(emotionText, x + cardPadding + 4, finalCardY + 42);

    ctx.restore();
  }

  // Utility to draw rounded rectangles
  function drawRoundedRect(context, x, y, width, height, radius) {
    context.beginPath();
    context.moveTo(x + radius, y);
    context.lineTo(x + width - radius, y);
    context.quadraticCurveTo(x + width, y, x + width, y + radius);
    context.lineTo(x + width, y + height - radius);
    context.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
    context.lineTo(x + radius, y + height);
    context.quadraticCurveTo(x, y + height, x, y + height - radius);
    context.lineTo(x, y + radius);
    context.quadraticCurveTo(x, y, x + radius, y);
    context.closePath();
  }

  // Snapshot Handling
  btnSnapshot.addEventListener('click', () => {
    if (!latestPayload || !latestPayload.image) return;

    snapshotImg.src = canvas.toDataURL('image/jpeg');
    downloadLink.href = snapshotImg.src;

    if (latestPayload.faces && latestPayload.faces.length > 0) {
      const f = latestPayload.faces[0];
      const emoji = emotionEmojis[f.emotion] || '😐';
      snapshotDetails.innerHTML = `
        <strong>Detection Summary:</strong><br>
        • Estimated Age: <strong>${f.age} years</strong><br>
        • Gender: <strong>${f.gender}</strong> (${f.gender_confidence}% confidence)<br>
        • Facial Emotion: <strong>${emoji} ${f.emotion}</strong> (${f.emotion_confidence}% confidence)
      `;
    } else {
      snapshotDetails.innerHTML = `No face detected in snapshot frame.`;
    }

    snapshotModal.classList.add('active');
  });

  modalCloseBtn.addEventListener('click', () => {
    snapshotModal.classList.remove('active');
  });

  // Start App
  connectWebSocket();
});
