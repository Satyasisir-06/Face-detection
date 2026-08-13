document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const video = document.getElementById('video-feed');
  const canvas = document.getElementById('view-canvas');
  const ctx = canvas.getContext('2d');
  const placeholder = document.getElementById('video-placeholder');
  const loadingText = document.getElementById('loading-text');
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
  let latestDetections = [];
  let modelsLoaded = false;
  let detecting = false;

  // Emotion Emojis Map
  const emotionEmojis = {
    'happy': '😊',
    'neutral': '😐',
    'surprised': '😲',
    'sad': '😢',
    'angry': '😡',
    'fearful': '😨',
    'disgusted': '🤢'
  };

  const emotionLabels = {
    'happy': 'Happy',
    'neutral': 'Neutral',
    'surprised': 'Surprise',
    'sad': 'Sad',
    'angry': 'Angry',
    'fearful': 'Fear',
    'disgusted': 'Disgust'
  };

  // MODEL_URL — face-api.js models hosted on jsDelivr CDN
  const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.14/model';

  // ─── 1. Load AI Models ───────────────────────────────────────────────
  async function loadModels() {
    loadingText.textContent = 'Loading AI Models...';
    try {
      await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
        faceapi.nets.ageGenderNet.loadFromUri(MODEL_URL),
        faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
      ]);
      modelsLoaded = true;
      loadingText.textContent = 'Starting Camera...';
      console.log('face-api.js models loaded successfully');
    } catch (err) {
      loadingText.textContent = 'Failed to load AI models. Please refresh.';
      console.error('Model loading error:', err);
    }
  }

  // ─── 2. Start Browser Camera ─────────────────────────────────────────
  async function startCamera() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
        audio: false,
      });
      video.srcObject = stream;
      await video.play();

      // Set canvas size to match video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      placeholder.style.display = 'none';
      cameraStatus.classList.add('online');
      cameraStatusText.textContent = 'Camera Active';

      // Start detection loop
      detectLoop();
    } catch (err) {
      console.error('Camera access error:', err);
      cameraStatusText.textContent = 'Camera Denied';
      loadingText.textContent = '⚠️ Camera access denied. Please allow camera permission and refresh.';
    }
  }

  // ─── 3. Detection Loop ───────────────────────────────────────────────
  async function detectLoop() {
    if (!modelsLoaded || video.paused || video.ended) {
      requestAnimationFrame(detectLoop);
      return;
    }

    // Skip if previous detection is still running
    if (detecting) {
      requestAnimationFrame(detectLoop);
      return;
    }

    detecting = true;
    const t0 = performance.now();

    try {
      const detections = await faceapi
        .detectAllFaces(video, new faceapi.TinyFaceDetectorOptions({
          inputSize: 320,
          scoreThreshold: 0.45,
        }))
        .withAgeAndGender()
        .withFaceExpressions();

      latestDetections = detections;

      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Update metrics
      const count = detections.length;
      faceCountVal.textContent = count;
      const latency = Math.round(performance.now() - t0);
      latencyVal.textContent = `${latency} ms`;

      // Draw detections
      detections.forEach((det) => {
        drawFaceBox(det);
      });

      // FPS calculation
      frameCount++;
      const now = performance.now();
      if (now - lastFpsCalcTime >= 1000) {
        const fps = Math.round((frameCount * 1000) / (now - lastFpsCalcTime));
        fpsCounter.textContent = `${fps} FPS`;
        frameCount = 0;
        lastFpsCalcTime = now;
      }
    } catch (err) {
      console.error('Detection error:', err);
    }

    detecting = false;
    requestAnimationFrame(detectLoop);
  }

  // ─── 4. Draw Face Bounding Box + Details Card ────────────────────────
  function drawFaceBox(detection) {
    const box = detection.detection.box;
    const x = box.x;
    const y = box.y;
    const w = box.width;
    const h = box.height;

    const age = Math.round(detection.age);
    const gender = detection.gender; // 'male' or 'female'
    const genderProb = Math.round(detection.genderProbability * 100);
    const genderLabel = gender === 'female' ? 'Female' : 'Male';

    // Get dominant expression
    const expressions = detection.expressions;
    let topEmotion = 'neutral';
    let topEmotionScore = 0;
    for (const [emotion, score] of Object.entries(expressions)) {
      if (score > topEmotionScore) {
        topEmotion = emotion;
        topEmotionScore = score;
      }
    }
    const emotionConf = Math.round(topEmotionScore * 100);
    const emoji = emotionEmojis[topEmotion] || '😐';
    const emotionLabel = emotionLabels[topEmotion] || topEmotion;

    ctx.save();

    // Color by gender
    const isFemale = gender === 'female';
    const primaryColor = isFemale ? '#ec4899' : '#38bdf8';

    // Bounding box
    ctx.strokeStyle = primaryColor;
    ctx.lineWidth = 3;
    ctx.shadowColor = primaryColor;
    ctx.shadowBlur = 12;
    ctx.strokeRect(x, y, w, h);

    // Corner accents
    const cornerSize = Math.min(w, h) * 0.2;
    ctx.lineWidth = 4;

    // Top-left
    ctx.beginPath();
    ctx.moveTo(x, y + cornerSize);
    ctx.lineTo(x, y);
    ctx.lineTo(x + cornerSize, y);
    ctx.stroke();

    // Bottom-right
    ctx.beginPath();
    ctx.moveTo(x + w - cornerSize, y + h);
    ctx.lineTo(x + w, y + h);
    ctx.lineTo(x + w, y + h - cornerSize);
    ctx.stroke();

    // Details card below bounding box
    const cardPadding = 10;
    const cardHeight = 54;
    const cardY = y + h + 6;
    const cardWidth = Math.max(w, 200);
    const finalCardY = (cardY + cardHeight > canvas.height) ? (y - cardHeight - 6) : cardY;

    // Dark glass card
    ctx.fillStyle = 'rgba(15, 23, 42, 0.88)';
    ctx.shadowColor = 'rgba(0, 0, 0, 0.7)';
    ctx.shadowBlur = 10;
    drawRoundedRect(ctx, x, finalCardY, cardWidth, cardHeight, 8);
    ctx.fill();

    // Left accent bar
    ctx.fillStyle = primaryColor;
    ctx.fillRect(x, finalCardY, 4, cardHeight);

    // Line 1: Gender & Age
    ctx.shadowBlur = 0;
    ctx.font = 'bold 15px Inter, sans-serif';
    ctx.fillStyle = '#ffffff';
    ctx.fillText(`${genderLabel} (${genderProb}%) • Age: ${age}`, x + cardPadding + 4, finalCardY + 22);

    // Line 2: Emotion
    ctx.font = '500 13px Inter, sans-serif';
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText(`${emoji} ${emotionLabel} (${emotionConf}%)`, x + cardPadding + 4, finalCardY + 42);

    ctx.restore();
  }

  // ─── 5. Rounded Rectangle Utility ────────────────────────────────────
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

  // ─── 6. Snapshot ─────────────────────────────────────────────────────
  btnSnapshot.addEventListener('click', () => {
    // Create a composite snapshot: video + canvas overlay
    const snapCanvas = document.createElement('canvas');
    snapCanvas.width = video.videoWidth;
    snapCanvas.height = video.videoHeight;
    const snapCtx = snapCanvas.getContext('2d');

    // Draw mirrored video frame
    snapCtx.save();
    snapCtx.scale(-1, 1);
    snapCtx.drawImage(video, -snapCanvas.width, 0, snapCanvas.width, snapCanvas.height);
    snapCtx.restore();

    // Draw overlay (bounding boxes)
    snapCtx.save();
    snapCtx.scale(-1, 1);
    snapCtx.drawImage(canvas, -snapCanvas.width, 0, snapCanvas.width, snapCanvas.height);
    snapCtx.restore();

    const dataUrl = snapCanvas.toDataURL('image/jpeg', 0.92);
    snapshotImg.src = dataUrl;
    downloadLink.href = dataUrl;

    // Fill details from latest detections
    if (latestDetections.length > 0) {
      const det = latestDetections[0];
      const age = Math.round(det.age);
      const gender = det.gender === 'female' ? 'Female' : 'Male';
      const genderConf = Math.round(det.genderProbability * 100);

      let topEmotion = 'neutral';
      let topScore = 0;
      for (const [emotion, score] of Object.entries(det.expressions)) {
        if (score > topScore) { topEmotion = emotion; topScore = score; }
      }
      const emoji = emotionEmojis[topEmotion] || '😐';
      const emotionLabel = emotionLabels[topEmotion] || topEmotion;

      snapshotDetails.innerHTML = `
        <strong>Detection Summary:</strong><br>
        • Estimated Age: <strong>${age} years</strong><br>
        • Gender: <strong>${gender}</strong> (${genderConf}% confidence)<br>
        • Emotion: <strong>${emoji} ${emotionLabel}</strong> (${Math.round(topScore * 100)}% confidence)<br>
        • Faces Detected: <strong>${latestDetections.length}</strong>
      `;
    } else {
      snapshotDetails.innerHTML = `No face detected in snapshot frame.`;
    }

    snapshotModal.classList.add('active');
  });

  modalCloseBtn.addEventListener('click', () => {
    snapshotModal.classList.remove('active');
  });

  // ─── 7. Initialise ──────────────────────────────────────────────────
  async function init() {
    await loadModels();
    if (modelsLoaded) {
      await startCamera();
    }
  }

  init();
});
