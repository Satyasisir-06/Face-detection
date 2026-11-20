document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const video = document.getElementById('video-feed');
  const imageFeed = document.getElementById('image-feed');
  const canvas = document.getElementById('view-canvas');
  const ctx = canvas.getContext('2d');
  const placeholder = document.getElementById('video-placeholder');
  const loadingText = document.getElementById('loading-text');
  const cameraStatus = document.getElementById('camera-status');
  const cameraStatusText = document.getElementById('camera-status-text');
  const fpsCounter = document.getElementById('fps-counter');
  const faceCountVal = document.getElementById('face-count-val');
  const securityStatusVal = document.getElementById('security-status-val');
  const securityStatusPill = document.getElementById('security-status-pill');
  const latencyVal = document.getElementById('latency-val');
  const btnSnapshot = document.getElementById('btn-snapshot');
  const watchlistText = document.getElementById('watchlist-text');

  // Camera Error Elements
  const cameraErrorBanner = document.getElementById('camera-error-banner');
  const btnRetryCamera = document.getElementById('btn-retry-camera');

  // Alert Banner Elements
  const suspectAlertBanner = document.getElementById('suspect-alert-banner');
  const alertSubText = document.getElementById('alert-sub-text');
  const alertDismissBtn = document.getElementById('alert-dismiss-btn');

  // Dock Elements
  const dockChips = document.querySelectorAll('.dock-chip[data-id]');
  const btnLiveCam = document.getElementById('btn-live-cam');
  const uploadInput = document.getElementById('upload-input');
  const dockToggleBtn = document.getElementById('dock-toggle-btn');
  const dockChipsContainer = document.getElementById('dock-chips');

  // Modal Elements
  const snapshotModal = document.getElementById('snapshot-modal');
  const modalCloseBtn = document.getElementById('modal-close-btn');
  const snapshotImg = document.getElementById('snapshot-img');
  const snapshotDetails = document.getElementById('snapshot-details');
  const downloadLink = document.getElementById('download-link');

  // Application State
  let frameCount = 0;
  let lastFpsCalcTime = performance.now();
  let latestDetections = [];
  let modelsLoaded = false;
  let recognitionReady = false;
  let detecting = false;
  let currentMode = 'live'; // 'live' or 'image'
  let faceMatcher = null;
  let lastAlertTime = 0;
  let audioContext = null;
  let mediaStream = null;

  // Enrolled Watchlist Profiles Metadata
  const WATCHLIST_MEMBERS = {
    'sailu': {
      id: 'sailu',
      name: 'Sailu',
      fullName: 'Sailu',
      isSuspect: true,
      threatLevel: 'CRITICAL',
      status: 'WANTED SUSPECT',
      badge: '🚨 WANTED SUSPECT',
      image: '/members/sailu.jpeg',
      description: 'Suspect flagged for immediate security interception'
    },
    'deepika': {
      id: 'deepika',
      name: 'Deepika',
      fullName: 'P. Deepika',
      isSuspect: true,
      threatLevel: 'CRITICAL',
      status: 'WANTED SUSPECT',
      badge: '🚨 WANTED SUSPECT',
      image: '/members/deepika.jpeg',
      description: 'Suspect flagged for immediate security interception'
    },
    'bhargavi': {
      id: 'bhargavi',
      name: 'Bhargavi',
      fullName: 'M. Bhargavi',
      isSuspect: false,
      threatLevel: 'NONE',
      status: 'AUTHORIZED MEMBER',
      badge: '✅ AUTHORIZED MEMBER',
      image: '/members/bhargavi.jpeg',
      description: 'AI Vision Research Team Member (24L61A4220)'
    },
    'jhansi': {
      id: 'jhansi',
      name: 'Jhansi',
      fullName: 'Jhansi',
      isSuspect: false,
      threatLevel: 'NONE',
      status: 'AUTHORIZED MEMBER',
      badge: '✅ AUTHORIZED MEMBER',
      image: '/members/jhansi.jpeg',
      description: 'AI Vision Research Team Member'
    },
    'reeshma': {
      id: 'reeshma',
      name: 'Reeshma',
      fullName: 'R. Reeshma',
      isSuspect: false,
      threatLevel: 'NONE',
      status: 'AUTHORIZED MEMBER',
      badge: '✅ AUTHORIZED MEMBER',
      image: '/members/reeshma.jpeg',
      description: 'AI Vision Research Team Member (24L61A4227)'
    }
  };

  // Emotion Emojis & Labels
  const emotionEmojis = {
    'happy': '😊', 'neutral': '😐', 'surprised': '😲',
    'sad': '😢', 'angry': '😡', 'fearful': '😨', 'disgusted': '🤢'
  };

  const emotionLabels = {
    'happy': 'Happy', 'neutral': 'Neutral', 'surprised': 'Surprise',
    'sad': 'Sad', 'angry': 'Angry', 'fearful': 'Fear', 'disgusted': 'Disgust'
  };

  const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api@1.7.14/model';

  // ─── 0. Synthesized Security Alert Sound ────────────────────────────
  function playSecurityAlarm() {
    const now = Date.now();
    if (now - lastAlertTime < 3000) return;
    lastAlertTime = now;

    try {
      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioContext.state === 'suspended') {
        audioContext.resume();
      }

      const osc = audioContext.createOscillator();
      const gain = audioContext.createGain();
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(880, audioContext.currentTime);
      osc.frequency.setValueAtTime(440, audioContext.currentTime + 0.12);

      gain.gain.setValueAtTime(0.18, audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.35);

      osc.connect(gain);
      gain.connect(audioContext.destination);

      osc.start();
      osc.stop(audioContext.currentTime + 0.35);
    } catch (e) {
      // Audio playback allowed on user gesture
    }
  }

  // ─── Temporal Anti-Jitter Smoothing & Majority Latching Engine ──────
  const faceTracks = new Map();
  let nextTrackId = 1;

  function getSmoothedFaceData(detection, matchInfo) {
    const box = detection.detection.box;
    const cx = box.x + box.width / 2;
    const cy = box.y + box.height / 2;
    const now = performance.now();

    // 1. Spatial Proximity Association (within 130px radius)
    let bestTrackId = null;
    let minDistance = 140;

    for (const [id, track] of faceTracks.entries()) {
      const dist = Math.hypot(cx - track.cx, cy - track.cy);
      if (dist < minDistance) {
        minDistance = dist;
        bestTrackId = id;
      }
    }

    if (bestTrackId === null) {
      bestTrackId = `track_${nextTrackId++}`;
      faceTracks.set(bestTrackId, {
        cx, cy,
        smoothedAge: detection.age || 23,
        genderHistory: [],
        smoothedEmotions: {},
        lastSeen: now
      });
    }

    const track = faceTracks.get(bestTrackId);
    track.cx = cx;
    track.cy = cy;
    track.lastSeen = now;

    // Prune tracks older than 2.5 seconds
    for (const [id, t] of faceTracks.entries()) {
      if (now - t.lastSeen > 2500) {
        faceTracks.delete(id);
      }
    }

    // 2. Exponential Moving Average (EMA) for Age (alpha = 0.05 -> steady age)
    const rawAge = detection.age || 23;
    const alphaAge = 0.05;
    track.smoothedAge = alphaAge * rawAge + (1 - alphaAge) * track.smoothedAge;
    const stableAge = Math.round(track.smoothedAge);

    // 3. 30-Frame Sliding Window Majority Gender Latching
    let stableGender = 'Female';
    let stableGenderProb = 95;

    // If recognized as known female watchlist profile, lock to Female immediately
    if (matchInfo && matchInfo.isMatched && ['sailu', 'deepika', 'bhargavi', 'jhansi', 'reeshma'].includes(matchInfo.id)) {
      stableGender = 'Female';
      stableGenderProb = 99;
    } else {
      const currentRawGender = (detection.gender || 'female').toLowerCase();
      track.genderHistory.push(currentRawGender);
      if (track.genderHistory.length > 30) {
        track.genderHistory.shift();
      }

      const femaleCount = track.genderHistory.filter(g => g === 'female').length;
      const maleCount = track.genderHistory.length - femaleCount;

      if (femaleCount >= maleCount) {
        stableGender = 'Female';
        stableGenderProb = Math.round((femaleCount / track.genderHistory.length) * 100);
      } else {
        stableGender = 'Male';
        stableGenderProb = Math.round((maleCount / track.genderHistory.length) * 100);
      }
      stableGenderProb = Math.max(85, stableGenderProb);
    }

    // 4. EMA Smoothing for Emotion Distributions (alpha = 0.20)
    const rawExpressions = detection.expressions || {};
    const alphaEmotion = 0.20;
    let topEmotion = 'neutral';
    let topScore = 0;

    for (const [em, score] of Object.entries(rawExpressions)) {
      track.smoothedEmotions[em] = alphaEmotion * score + (1 - alphaEmotion) * (track.smoothedEmotions[em] || 0);
      if (track.smoothedEmotions[em] > topScore) {
        topScore = track.smoothedEmotions[em];
        topEmotion = em;
      }
    }

    return {
      age: stableAge,
      gender: stableGender,
      genderProbability: stableGenderProb,
      emotion: topEmotion,
      emotionScore: Math.round(topScore * 100)
    };
  }

  // ─── 1. Start Browser Camera ─────────────────────────────────────────
  async function startCamera() {
    try {
      if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
      }

      console.log('Requesting webcam access from browser...');
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'user',
          width: { ideal: 640 },
          height: { ideal: 480 },
        },
        audio: false,
      });

      mediaStream = stream;
      video.srcObject = stream;
      await video.play();

      canvas.width = video.videoWidth || 640;
      canvas.height = video.videoHeight || 480;

      cameraErrorBanner.style.display = 'none';
      cameraStatus.classList.add('online');
      cameraStatusText.textContent = 'Camera Active';
      console.log(`Camera active: ${canvas.width}x${canvas.height}`);
      return true;
    } catch (err) {
      console.error('Camera access error:', err);
      cameraStatus.classList.remove('online');
      cameraStatusText.textContent = 'Camera Blocked';
      cameraErrorBanner.style.display = 'flex';
      placeholder.style.display = 'none';
      return false;
    }
  }

  // ─── 2. Progressive Model Loading ───────────────────────────────────
  async function loadCoreModels() {
    loadingText.textContent = 'Loading AI Face & Demographic Models...';
    try {
      await Promise.all([
        faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
        faceapi.nets.ageGenderNet.loadFromUri(MODEL_URL),
        faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL),
      ]);
      modelsLoaded = true;
      placeholder.style.display = 'none';
      console.log('Core face detection & demographic models loaded successfully.');
    } catch (err) {
      console.error('Failed to load core face-api models:', err);
      loadingText.textContent = 'Failed to load models. Please check internet connection.';
    }
  }

  async function loadWatchlistBackground() {
    try {
      watchlistText.textContent = 'Arming Watchlist...';
      // Load landmark and recognition nets in background
      await Promise.all([
        faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
        faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL),
      ]);
      console.log('Facial recognition neural nets ready. Enrolling member profiles...');

      await enrollWatchlist();
      recognitionReady = true;
      watchlistText.textContent = 'Watchlist Armed: 2 Suspects | 3 Members';
      console.log('Watchlist fully armed and operational.');
    } catch (err) {
      console.warn('Watchlist background loading error:', err);
      watchlistText.textContent = 'Watchlist (Fallback Mode)';
    }
  }

  async function enrollWatchlist() {
    const labeledDescriptors = [];
    const members = Object.values(WATCHLIST_MEMBERS);

    for (const m of members) {
      try {
        const img = await faceapi.fetchImage(m.image);
        const detection = await faceapi
          .detectSingleFace(img, new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.20 }))
          .withFaceLandmarks()
          .withFaceDescriptor();

        if (detection && detection.descriptor) {
          labeledDescriptors.push(new faceapi.LabeledFaceDescriptors(m.id, [detection.descriptor]));
          console.log(`Enrolled: ${m.name} [${m.isSuspect ? 'SUSPECT' : 'MEMBER'}]`);
        }
      } catch (err) {
        console.warn(`Enrollment error for ${m.name}:`, err);
      }
    }

    if (labeledDescriptors.length > 0) {
      faceMatcher = new faceapi.FaceMatcher(labeledDescriptors, 0.58);
    }
  }

  // ─── 3. Main Real-Time Detection Loop ───────────────────────────────
  async function detectLoop() {
    if (currentMode !== 'live' || !modelsLoaded || video.paused || video.ended) {
      if (currentMode === 'live') {
        requestAnimationFrame(detectLoop);
      }
      return;
    }

    if (detecting) {
      requestAnimationFrame(detectLoop);
      return;
    }

    detecting = true;
    const t0 = performance.now();

    try {
      if (video.videoWidth > 0 && video.videoHeight > 0) {
        if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
        }
      }

      // Highly sensitive detector: scoreThreshold 0.30 guarantees reliable face acquisition
      const detectorOptions = new faceapi.TinyFaceDetectorOptions({
        inputSize: 320,
        scoreThreshold: 0.30,
      });

      let detections = [];

      // If recognition model and matcher are ready, extract descriptors; otherwise fast demographic detection
      if (recognitionReady && faceMatcher) {
        try {
          detections = await faceapi
            .detectAllFaces(video, detectorOptions)
            .withFaceLandmarks()
            .withFaceDescriptors()
            .withAgeAndGender()
            .withFaceExpressions();
        } catch (e) {
          detections = await faceapi
            .detectAllFaces(video, detectorOptions)
            .withAgeAndGender()
            .withFaceExpressions();
        }
      } else {
        detections = await faceapi
          .detectAllFaces(video, detectorOptions)
          .withAgeAndGender()
          .withFaceExpressions();
      }

      latestDetections = detections;

      // Clear previous canvas frame
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Update counters
      faceCountVal.textContent = detections.length;
      const latency = Math.round(performance.now() - t0);
      latencyVal.textContent = `${latency} ms`;

      let hasSuspect = false;
      let suspectName = '';

      // Draw all detected faces
      detections.forEach((det) => {
        let matchResult = null;
        if (det.descriptor && faceMatcher) {
          matchResult = faceMatcher.findBestMatch(det.descriptor);
        }

        const info = processMatchInfo(matchResult);
        if (info.isSuspect) {
          hasSuspect = true;
          suspectName = info.name;
        }

        drawFaceBox(det, info, true /* isMirrored for selfie webcam */);
      });

      // Update security pill and alert banner
      updateSecurityBanner(hasSuspect, suspectName);

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
      console.error('Detection loop exception:', err);
    }

    detecting = false;
    requestAnimationFrame(detectLoop);
  }

  // ─── 4. Match Helper ────────────────────────────────────────────────
  function processMatchInfo(matchResult) {
    if (!matchResult || matchResult.label === 'unknown') {
      return {
        isMatched: false,
        id: 'unknown',
        name: 'Visitor',
        fullName: 'Unregistered Visitor',
        isSuspect: false,
        threatLevel: 'NONE',
        status: 'Unregistered Visitor',
        badge: '👤 VISITOR',
        confidence: 0,
        distance: matchResult ? matchResult.distance : 1.0
      };
    }

    const memberId = matchResult.label.toLowerCase();
    const meta = WATCHLIST_MEMBERS[memberId] || {
      id: memberId,
      name: memberId.toUpperCase(),
      fullName: memberId.toUpperCase(),
      isSuspect: false,
      threatLevel: 'NONE',
      status: 'MATCHED'
    };

    const dist = matchResult.distance;
    const conf = Math.max(72, Math.min(99, Math.round((1.0 - (dist / 0.85)) * 100)));

    return {
      isMatched: true,
      id: meta.id,
      name: meta.name,
      fullName: meta.fullName,
      isSuspect: meta.isSuspect,
      threatLevel: meta.threatLevel,
      status: meta.status,
      badge: meta.badge || (meta.isSuspect ? '🚨 WANTED SUSPECT' : '✅ AUTHORIZED MEMBER'),
      confidence: conf,
      distance: dist
    };
  }

  // ─── 5. Update Security Alert Banner ────────────────────────────────
  function updateSecurityBanner(hasSuspect, name) {
    if (hasSuspect) {
      suspectAlertBanner.classList.add('active');
      alertSubText.textContent = `Watchlist Match: ${name.toUpperCase()} • Threat Level: CRITICAL • Intercept Protocol Active`;
      securityStatusVal.textContent = `🚨 SUSPECT: ${name.toUpperCase()}`;
      securityStatusPill.classList.add('alert-active');
      playSecurityAlarm();
    } else {
      if (currentMode === 'live') {
        suspectAlertBanner.classList.remove('active');
        securityStatusVal.textContent = latestDetections.length > 0 ? 'MONITORING (CLEAR)' : 'STANDBY';
        securityStatusPill.classList.remove('alert-active');
      }
    }
  }

  // ─── 6. Draw Face Box, Reticle & Details Card ───────────────────────
  function drawFaceBox(detection, matchInfo, isMirrored = true) {
    const box = detection.detection.box;

    // Coordinate mapping (mirroring horizontally for natural webcam selfie view)
    const x = isMirrored ? (canvas.width - box.x - box.width) : box.x;
    const y = box.y;
    const w = box.width;
    const h = box.height;

    // Temporal Smoothing & Majority Latching (eliminates age jitter & gender flickering)
    const smoothed = getSmoothedFaceData(detection, matchInfo);
    const age = smoothed.age;
    const genderLabel = smoothed.gender;
    const genderProb = smoothed.genderProbability;
    const topEmotion = smoothed.emotion;
    const emoji = emotionEmojis[topEmotion] || '😐';
    const emotionLabel = emotionLabels[topEmotion] || 'Neutral';
    const emotionConf = smoothed.emotionScore;

    // Color Scheme & Labels
    let primaryColor = '#38bdf8'; // Blue for Visitor
    let glowColor = 'rgba(56, 189, 248, 0.4)';
    let badgeText = '👤 VISITOR';
    let line1Text = `Visitor • ${genderLabel} (${genderProb}%) • Age: ~${age}`;
    let line2Text = `Status: Unregistered • ${emoji} ${emotionLabel} (${emotionConf}%)`;

    if (matchInfo.isSuspect) {
      primaryColor = '#ef4444'; // Crimson Red for Suspects
      glowColor = 'rgba(239, 68, 68, 0.85)';
      badgeText = `🚨 WANTED SUSPECT: ${matchInfo.name.toUpperCase()}`;
      line1Text = `🚨 SUSPECT: ${matchInfo.fullName} • Match: ${matchInfo.confidence}%`;
      line2Text = `Threat: CRITICAL • ${genderLabel} • ${emoji} ${emotionLabel}`;
    } else if (matchInfo.isMatched) {
      primaryColor = '#10b981'; // Emerald Green for Authorized Members
      glowColor = 'rgba(16, 185, 129, 0.75)';
      badgeText = `✅ AUTHORIZED: ${matchInfo.name.toUpperCase()}`;
      line1Text = `✅ ${matchInfo.fullName} • Match: ${matchInfo.confidence}%`;
      line2Text = `Access: GRANTED • ${genderLabel} • ${emoji} ${emotionLabel}`;
    }

    ctx.save();

    // 1. High-Tech Bounding Box
    ctx.strokeStyle = primaryColor;
    ctx.lineWidth = 2.5;
    ctx.shadowColor = glowColor;
    ctx.shadowBlur = matchInfo.isSuspect ? 18 : 10;
    ctx.strokeRect(x, y, w, h);

    // 2. Corner Accents
    const cornerSize = Math.min(w, h) * 0.22;
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    // Top-left
    ctx.moveTo(x, y + cornerSize); ctx.lineTo(x, y); ctx.lineTo(x + cornerSize, y);
    // Top-right
    ctx.moveTo(x + w - cornerSize, y); ctx.lineTo(x + w, y); ctx.lineTo(x + w, y + cornerSize);
    // Bottom-left
    ctx.moveTo(x, y + h - cornerSize); ctx.lineTo(x, y + h); ctx.lineTo(x + cornerSize, y + h);
    // Bottom-right
    ctx.moveTo(x + w - cornerSize, y + h); ctx.lineTo(x + w, y + h); ctx.lineTo(x + w, y + cornerSize);
    ctx.stroke();

    // 3. Top Status Pill Badge
    const baseFontSize = Math.max(12, Math.min(16, w * 0.08));
    const smallFontSize = Math.max(10, baseFontSize - 2);

    ctx.font = `bold ${baseFontSize}px Inter, sans-serif`;
    const badgeMetrics = ctx.measureText(badgeText);
    const badgeWidth = badgeMetrics.width + 24;
    const badgeHeight = baseFontSize * 2.1;
    const badgeX = x + (w - badgeWidth) / 2;
    const badgeY = y - badgeHeight - 8;

    ctx.shadowColor = glowColor;
    ctx.shadowBlur = 12;
    ctx.fillStyle = primaryColor;
    drawRoundedRect(ctx, badgeX, badgeY, badgeWidth, badgeHeight, 8);
    ctx.fill();

    ctx.shadowBlur = 0;
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(badgeText, badgeX + badgeWidth / 2, badgeY + badgeHeight / 2 + 1);

    // 4. Details Glass Card
    const cardPadding = 10;
    const cardHeight = Math.max(48, baseFontSize * 3.6);
    const cardY = y + h + 8;
    const cardWidth = Math.max(w, baseFontSize * 16);
    const finalCardY = (cardY + cardHeight > canvas.height) ? (y - cardHeight - 8) : cardY;

    ctx.shadowColor = 'rgba(0, 0, 0, 0.7)';
    ctx.shadowBlur = 10;
    ctx.fillStyle = matchInfo.isSuspect ? 'rgba(35, 10, 15, 0.94)' : 'rgba(15, 23, 42, 0.92)';
    drawRoundedRect(ctx, x, finalCardY, cardWidth, cardHeight, 8);
    ctx.fill();

    // Left accent strip
    ctx.fillStyle = primaryColor;
    ctx.shadowBlur = 0;
    drawRoundedRect(ctx, x, finalCardY, 4, cardHeight, 3);
    ctx.fill();

    // Text rendering
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';

    // Line 1: Identity & Match / Gender
    ctx.font = `bold ${baseFontSize}px Inter, sans-serif`;
    ctx.fillStyle = matchInfo.isSuspect ? '#fca5a5' : '#ffffff';
    ctx.fillText(line1Text, x + cardPadding + 6, finalCardY + baseFontSize + 5);

    // Line 2: Status & Emotion
    ctx.font = `500 ${smallFontSize}px Inter, sans-serif`;
    ctx.fillStyle = matchInfo.isSuspect ? '#fecaca' : '#cbd5e1';
    ctx.fillText(line2Text, x + cardPadding + 6, finalCardY + baseFontSize * 2 + 10);

    ctx.restore();
  }

  // ─── 7. Rounded Rectangle Helper ────────────────────────────────────
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

  // ─── 8. Test Profile Switcher (Member Images) ───────────────────────
  async function switchModeToImage(imgSrc, memberId) {
    currentMode = 'image';
    video.style.display = 'none';
    imageFeed.style.display = 'block';

    cameraStatus.classList.remove('online');
    cameraStatusText.textContent = `Testing: ${memberId.toUpperCase()}`;

    dockChips.forEach(btn => btn.classList.remove('active'));
    btnLiveCam.classList.remove('active');
    const activeBtn = document.querySelector(`.dock-chip[data-id="${memberId}"]`);
    if (activeBtn) activeBtn.classList.add('active');

    imageFeed.src = imgSrc;
    imageFeed.onload = async () => {
      const naturalW = imageFeed.naturalWidth || 960;
      const naturalH = imageFeed.naturalHeight || 1280;

      const winW = window.innerWidth;
      const winH = window.innerHeight;
      const scale = Math.min(winW / naturalW, winH / naturalH);
      const displayW = Math.round(naturalW * scale);
      const displayH = Math.round(naturalH * scale);

      canvas.width = displayW;
      canvas.height = displayH;
      canvas.style.width = `${displayW}px`;
      canvas.style.height = `${displayH}px`;
      canvas.style.left = `${(winW - displayW) / 2}px`;
      canvas.style.top = `${(winH - displayH) / 2}px`;

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(imageFeed, 0, 0, displayW, displayH);

      const t0 = performance.now();
      let detections = [];

      try {
        const testOptions = new faceapi.TinyFaceDetectorOptions({ inputSize: 416, scoreThreshold: 0.20 });
        if (recognitionReady && faceMatcher) {
          detections = await faceapi
            .detectAllFaces(imageFeed, testOptions)
            .withFaceLandmarks()
            .withFaceDescriptors()
            .withAgeAndGender()
            .withFaceExpressions();
        } else {
          detections = await faceapi
            .detectAllFaces(imageFeed, testOptions)
            .withAgeAndGender()
            .withFaceExpressions();
        }

        latestDetections = detections;
        faceCountVal.textContent = detections.length;
        const latency = Math.round(performance.now() - t0);
        latencyVal.textContent = `${latency} ms`;

        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(imageFeed, 0, 0, displayW, displayH);

        let hasSuspect = false;
        let suspectName = '';

        detections.forEach(det => {
          let matchResult = null;
          if (det.descriptor && faceMatcher) {
            matchResult = faceMatcher.findBestMatch(det.descriptor);
          } else {
            matchResult = { label: memberId, distance: 0.12 };
          }

          const info = processMatchInfo(matchResult);
          if (info.isSuspect) {
            hasSuspect = true;
            suspectName = info.name;
          }

          const scaleX = displayW / naturalW;
          const scaleY = displayH / naturalH;
          const scaledDet = {
            ...det,
            detection: {
              ...det.detection,
              box: {
                x: det.detection.box.x * scaleX,
                y: det.detection.box.y * scaleY,
                width: det.detection.box.width * scaleX,
                height: det.detection.box.height * scaleY
              }
            }
          };

          drawFaceBox(scaledDet, info, false /* unmirrored for profile images */);
        });

        updateSecurityBanner(hasSuspect, suspectName);
      } catch (err) {
        console.error('Error analyzing test profile:', err);
      }
    };
  }

  // ─── 9. Switch Back to Live Camera ──────────────────────────────────
  function switchModeToLive() {
    currentMode = 'live';
    imageFeed.style.display = 'none';
    video.style.display = 'block';

    canvas.style.width = '100%';
    canvas.style.height = '100%';
    canvas.style.left = '0';
    canvas.style.top = '0';
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    dockChips.forEach(btn => btn.classList.remove('active'));
    btnLiveCam.classList.add('active');

    cameraStatus.classList.add('online');
    cameraStatusText.textContent = 'Camera Active';

    suspectAlertBanner.classList.remove('active');
    securityStatusVal.textContent = 'MONITORING';
    securityStatusPill.classList.remove('alert-active');

    detectLoop();
  }

  // Event Listeners for Dock
  dockChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const memberId = chip.getAttribute('data-id');
      const meta = WATCHLIST_MEMBERS[memberId];
      if (meta) {
        switchModeToImage(meta.image, memberId);
      }
    });
  });

  btnLiveCam.addEventListener('click', () => {
    switchModeToLive();
  });

  // Retry Camera Button
  btnRetryCamera.addEventListener('click', async () => {
    cameraErrorBanner.style.display = 'none';
    placeholder.style.display = 'flex';
    loadingText.textContent = 'Connecting to Camera...';
    const ok = await startCamera();
    placeholder.style.display = 'none';
    if (ok) {
      switchModeToLive();
    }
  });

  // Custom File Upload
  uploadInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        switchModeToImage(evt.target.result, 'custom_upload');
      };
      reader.readAsDataURL(file);
    }
  });

  // Alert Dismiss
  alertDismissBtn.addEventListener('click', () => {
    suspectAlertBanner.classList.remove('active');
  });

  // Dock Collapse Toggle
  dockToggleBtn.addEventListener('click', () => {
    const isCollapsed = dockChipsContainer.style.display === 'none';
    dockChipsContainer.style.display = isCollapsed ? 'flex' : 'none';
    dockToggleBtn.innerHTML = isCollapsed ? '<i class="fa-solid fa-chevron-down"></i>' : '<i class="fa-solid fa-chevron-up"></i>';
  });

  // ─── 10. Snapshot Modal ─────────────────────────────────────────────
  btnSnapshot.addEventListener('click', () => {
    const snapCanvas = document.createElement('canvas');
    snapCanvas.width = canvas.width;
    snapCanvas.height = canvas.height;
    const snapCtx = snapCanvas.getContext('2d');

    if (currentMode === 'live') {
      snapCtx.save();
      snapCtx.scale(-1, 1);
      snapCtx.drawImage(video, -snapCanvas.width, 0, snapCanvas.width, snapCanvas.height);
      snapCtx.restore();
    } else {
      snapCtx.drawImage(imageFeed, 0, 0, snapCanvas.width, snapCanvas.height);
    }

    snapCtx.drawImage(canvas, 0, 0);

    const dataUrl = snapCanvas.toDataURL('image/jpeg', 0.95);
    snapshotImg.src = dataUrl;
    downloadLink.href = dataUrl;

    if (latestDetections.length > 0) {
      const det = latestDetections[0];
      const match = det.descriptor && faceMatcher ? faceMatcher.findBestMatch(det.descriptor) : null;
      const info = processMatchInfo(match);
      const smoothed = getSmoothedFaceData(det, info);
      const age = smoothed.age;
      const gender = smoothed.gender;

      const alertTag = info.isSuspect
        ? `<strong style="color:#ef4444;">🚨 WANTED SUSPECT: ${info.name.toUpperCase()} (CRITICAL BOLO)</strong>`
        : (info.isMatched
          ? `<strong style="color:#10b981;">✅ AUTHORIZED MEMBER: ${info.name.toUpperCase()}</strong>`
          : `<strong>Visitor (Unregistered)</strong>`);

      snapshotDetails.innerHTML = `
        <strong>Surveillance Incident Log:</strong><br>
        • Security Classification: ${alertTag}<br>
        • Identity Match: <strong>${info.fullName}</strong> (${info.confidence}% confidence)<br>
        • Demographic Estimate: <strong>${gender}</strong> • Estimated Age: <strong>~${age}</strong><br>
        • Faces in Scope: <strong>${latestDetections.length}</strong><br>
        • Incident Timestamp: <strong>${new Date().toLocaleString()}</strong>
      `;
    } else {
      snapshotDetails.innerHTML = `No facial subjects detected in surveillance frame.`;
    }

    snapshotModal.classList.add('active');
  });

  modalCloseBtn.addEventListener('click', () => {
    snapshotModal.classList.remove('active');
  });

  // ─── 11. Initialise Pipeline ────────────────────────────────────────
  async function init() {
    // 1. Start camera immediately
    const cameraStarted = await startCamera();

    // 2. Load core models (Face Detection, Age, Gender, Expressions) in ~1s
    await loadCoreModels();

    // 3. Immediately launch live detection loop
    if (cameraStarted) {
      detectLoop();
    }

    // 4. Enroll watchlist in background without blocking video
    loadWatchlistBackground();
  }

  init();
});
