/**
 * MediaPipe Hand Landmarker（@mediapipe/tasks-vision）+ Canvas
 * 摄像头开启后实时绘制：红关节点、绿色荧光骨架
 */
(function (global) {
  'use strict';

  const TASKS_VISION_VER = '0.10.18';
  const TASKS_VISION_ESM = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${TASKS_VISION_VER}/+esm`;

  const WRIST = 0;

  const HAND_CONNECTIONS = [
    [0, 1], [1, 2], [2, 3], [3, 4],
    [0, 5], [5, 6], [6, 7], [7, 8],
    [5, 9], [9, 10], [10, 11], [11, 12],
    [9, 13], [13, 14], [14, 15], [15, 16],
    [13, 17], [17, 18], [18, 19], [19, 20],
    [0, 17],
  ];

  const STYLE = {
    boneColor: '#00ff00',
    boneWidth: 2,
    boneGlowOuter: '#00ff00',
    boneGlowBlur: 6,
    boneOuterExtra: 1,
    jointColor: '#ff3333',
    jointRadius: 5,
    hudColor: '#2196f3',
  };

  function avgLandmark(points, indices) {
    let x = 0;
    let y = 0;
    indices.forEach((i) => {
      x += points[i].x;
      y += points[i].y;
    });
    return { x: x / indices.length, y: y / indices.length, z: 0 };
  }

  function to24Landmarks(landmarks) {
    if (!landmarks || landmarks.length < 21) return landmarks || [];
    const palmCenter = avgLandmark(landmarks, [0, 5, 9, 13, 17]);
    const thumbWeb = {
      x: (landmarks[1].x + landmarks[5].x) / 2,
      y: (landmarks[1].y + landmarks[5].y) / 2,
      z: 0,
    };
    const knuckleCenter = avgLandmark(landmarks, [5, 9, 13]);
    return landmarks.slice(0, 21).concat([palmCenter, thumbWeb, knuckleCenter]);
  }

  function computeCoverTransform(videoW, videoH, displayW, displayH) {
    if (!videoW || !videoH || !displayW || !displayH) {
      return { scale: 1, offsetX: 0, offsetY: 0 };
    }
    const videoAspect = videoW / videoH;
    const displayAspect = displayW / displayH;
    let scale;
    let offsetX = 0;
    let offsetY = 0;
    if (videoAspect > displayAspect) {
      scale = displayH / videoH;
      offsetX = (displayW - videoW * scale) / 2;
    } else {
      scale = displayW / videoW;
      offsetY = (displayH - videoH * scale) / 2;
    }
    return { scale, offsetX, offsetY };
  }

  class HandLandmarkTracker {
    constructor(videoEl, canvasEl, badgeEl, options) {
      this.video = videoEl;
      this.canvas = canvasEl;
      this.badge = badgeEl;
      this.ctx = canvasEl.getContext('2d');
      this.options = options || {};
      this.modelUrl =
        this.options.modelUrl || '/static/sign_app/mediapipe/hand_landmarker.task';
      this.wasmBaseUrl =
        this.options.wasmBaseUrl ||
        `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${TASKS_VISION_VER}/wasm`;
      this.landmarker = null;
      this.running = false;
      this.enabled = true;
      this.rafId = null;
      this.initPromise = null;
      this.lastVideoTime = -1;
      this.displayTransform = { scale: 1, offsetX: 0, offsetY: 0 };
      this.fps = 0;
      this._fpsFrames = 0;
      this._fpsLast = performance.now();
      this._onLayout = () => this._resizeCanvas();
    }

    init() {
      if (!this.initPromise) {
        this.initPromise = this._doInit();
      }
      return this.initPromise;
    }

    ensureReady() {
      return this.init();
    }

    async _doInit() {
      this._setBadge('正在加载 MediaPipe 模型…');
      let HandLandmarker;
      let FilesetResolver;
      try {
        const mod = await import(/* webpackIgnore: true */ TASKS_VISION_ESM);
        HandLandmarker = mod.HandLandmarker;
        FilesetResolver = mod.FileSetResolver || mod.FilesetResolver;
      } catch (e) {
        this._setBadge('MediaPipe 库加载失败（请检查网络）', true);
        throw e;
      }

      const vision = await FilesetResolver.forVisionTasks(this.wasmBaseUrl);
      const base = {
        modelAssetPath: this.modelUrl,
      };

      const tryCreate = async (delegate) => {
        return HandLandmarker.createFromOptions(vision, {
          baseOptions: { ...base, delegate },
          runningMode: 'VIDEO',
          numHands: 2,
          minHandDetectionConfidence: 0.4,
          minHandPresenceConfidence: 0.4,
          minTrackingConfidence: 0.4,
        });
      };

      try {
        this.landmarker = await tryCreate('GPU');
      } catch (gpuErr) {
        console.warn('GPU  delegate 失败，改用 CPU', gpuErr);
        this.landmarker = await tryCreate('CPU');
      }

      this.video.addEventListener('loadedmetadata', this._onLayout);
      window.addEventListener('resize', this._onLayout);
      this._setBadge('MediaPipe 已就绪 · 等待手部');
    }

    _setBadge(text, isError) {
      if (!this.badge) return;
      this.badge.textContent = text;
      if (isError) {
        this.badge.style.borderColor = 'rgba(244, 67, 54, 0.6)';
        this.badge.style.color = '#ef9a9a';
      } else {
        this.badge.style.borderColor = 'rgba(33, 150, 243, 0.4)';
        this.badge.style.color = '#64b5f6';
      }
    }

    setEnabled(on) {
      this.enabled = !!on;
      if (!this.enabled) {
        this._clearCanvas();
        this._setBadge('MediaPipe 已就绪 · 等待手部');
      }
    }

    async start() {
      await this.ensureReady();
      if (this.running || !this.landmarker) return;
      await this._waitForVideoFrame();
      this.running = true;
      this.lastVideoTime = -1;
      this._resizeCanvas();
      this._setBadge('正在检测手部…');
      this._loop();
    }

    stop() {
      this.running = false;
      if (this.rafId) {
        cancelAnimationFrame(this.rafId);
        this.rafId = null;
      }
      this._clearCanvas();
      this._setBadge('MediaPipe 已就绪 · 等待手部');
      this.fps = 0;
    }

    _waitForVideoFrame() {
      return new Promise((resolve) => {
        const ok = () =>
          this.video.readyState >= 2 &&
          this.video.videoWidth > 0 &&
          this.video.videoHeight > 0;
        if (ok()) {
          resolve();
          return;
        }
        const done = () => {
          if (ok()) {
            this.video.removeEventListener('loadeddata', done);
            this.video.removeEventListener('loadedmetadata', done);
            resolve();
          }
        };
        this.video.addEventListener('loadeddata', done);
        this.video.addEventListener('loadedmetadata', done);
      });
    }

    _loop() {
      if (!this.running) return;

      const vw = this.video.videoWidth;
      const vh = this.video.videoHeight;
      if (
        this.enabled &&
        this.landmarker &&
        this.video.readyState >= 2 &&
        vw > 0 &&
        vh > 0 &&
        this.video.currentTime !== this.lastVideoTime
      ) {
        this.lastVideoTime = this.video.currentTime;
        try {
          const results = this.landmarker.detectForVideo(
            this.video,
            performance.now()
          );
          this._drawResults(results);
          this._tickFps();
        } catch (e) {
          console.warn('手部检测帧失败', e);
        }
      }

      this.rafId = requestAnimationFrame(() => this._loop());
    }

    _resizeCanvas() {
      const cw = this.canvas.clientWidth || 640;
      const ch = this.canvas.clientHeight || 360;
      if (cw > 0 && ch > 0) {
        this.canvas.width = cw;
        this.canvas.height = ch;
      }
      this.displayTransform = computeCoverTransform(
        this.video.videoWidth,
        this.video.videoHeight,
        this.canvas.width,
        this.canvas.height
      );
    }

    _toCanvas(lm) {
      const { scale, offsetX, offsetY } = this.displayTransform;
      const vw = this.video.videoWidth || 1;
      const vh = this.video.videoHeight || 1;
      return {
        x: lm.x * vw * scale + offsetX,
        y: lm.y * vh * scale + offsetY,
      };
    }

    _clearCanvas() {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    _tickFps() {
      this._fpsFrames += 1;
      const now = performance.now();
      if (now - this._fpsLast >= 1000) {
        this.fps = this._fpsFrames;
        this._fpsFrames = 0;
        this._fpsLast = now;
      }
    }

    _drawResults(results) {
      this._resizeCanvas();
      const ctx = this.ctx;
      const w = this.canvas.width;
      const h = this.canvas.height;
      ctx.clearRect(0, 0, w, h);

      const hands = results.landmarks || [];
      if (!hands.length) {
        this._drawHud(ctx, 0);
        this._setBadge('未检测到手 · 请将手掌对准镜头');
        return;
      }

      let totalPoints = 0;
      hands.forEach((landmarks, handIdx) => {
        totalPoints += to24Landmarks(landmarks).length;
        this._drawBones(ctx, landmarks);
        landmarks.forEach((lm, idx) => {
          if (idx > 20) return;
          const p = this._toCanvas(lm);
          this._drawJoint(ctx, p.x, p.y);
        });
        const wrist = this._toCanvas(landmarks[WRIST]);
        this._drawWristMark(ctx, wrist.x, wrist.y, handIdx);
      });

      this._drawHud(ctx, totalPoints);
      this._setBadge(`${totalPoints} 点 · ${hands.length} 只手 · ${this.fps} FPS`);
    }

    _drawBones(ctx, landmarks) {
      const drawPass = (width, color, blur) => {
        ctx.save();
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.strokeStyle = color;
        ctx.lineWidth = width;
        ctx.shadowColor = color;
        ctx.shadowBlur = blur;
        HAND_CONNECTIONS.forEach(([a, b]) => {
          if (!landmarks[a] || !landmarks[b]) return;
          const p1 = this._toCanvas(landmarks[a]);
          const p2 = this._toCanvas(landmarks[b]);
          ctx.beginPath();
          ctx.moveTo(p1.x, p1.y);
          ctx.lineTo(p2.x, p2.y);
          ctx.stroke();
        });
        ctx.restore();
      };
      drawPass(STYLE.boneWidth + STYLE.boneOuterExtra, STYLE.boneGlowOuter, STYLE.boneGlowBlur);
      drawPass(STYLE.boneWidth, STYLE.boneColor, STYLE.boneGlowBlur - 2);
    }

    _drawJoint(ctx, x, y) {
      ctx.save();
      ctx.beginPath();
      ctx.arc(x, y, STYLE.jointRadius + 1, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(255,255,255,0.85)';
      ctx.fill();
      ctx.beginPath();
      ctx.arc(x, y, STYLE.jointRadius, 0, Math.PI * 2);
      ctx.fillStyle = STYLE.jointColor;
      ctx.fill();
      ctx.restore();
    }

    _drawWristMark(ctx, x, y, handIdx) {
      const off = handIdx === 0 ? -18 : 18;
      const cx = x + off;
      const cy = y - 12;
      ctx.save();
      ctx.strokeStyle = STYLE.hudColor;
      ctx.lineWidth = 2;
      const s = 6;
      ctx.beginPath();
      ctx.moveTo(cx - s, cy);
      ctx.lineTo(cx + s, cy);
      ctx.moveTo(cx, cy - s);
      ctx.lineTo(cx, cy + s);
      ctx.stroke();
      ctx.restore();
    }

    _drawHud(ctx, count) {
      ctx.save();
      ctx.font = 'bold 28px "Segoe UI", Arial, sans-serif';
      ctx.fillStyle = STYLE.hudColor;
      ctx.shadowColor = 'rgba(33, 150, 243, 0.6)';
      ctx.shadowBlur = 6;
      ctx.fillText(String(count), 14, 36);
      ctx.restore();
    }
  }

  global.HandLandmarkTracker = HandLandmarkTracker;
  global.HAND_LANDMARKS_PER_HAND = 24;
})(window);
