export class InterviewWebSocketService {
  constructor(sessionId, onMetricsUpdate) {
    this.sessionId = sessionId;
    this.onMetricsUpdate = onMetricsUpdate;
    this.ws = null;
    this.isConnected = false;
    this.isFrameInFlight = false;
    this.lastFrameSentTime = 0;
    this.reconnectTimer = null;
    this.pingTimer = null;
    this.isClosedManually = false;
  }

  connect() {
    this.isClosedManually = false;
    const host = window.location.hostname || 'localhost';
    const port = '8000';
    const wsUrl = `ws://${host}:${port}/ws/interview/${this.sessionId}`;

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected for session:', this.sessionId);
        this.isConnected = true;
        this.isFrameInFlight = false;

        // Keep-alive ping every 5 seconds
        clearInterval(this.pingTimer);
        this.pingTimer = setInterval(() => {
          if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 5000);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'vision_update') {
            this.isFrameInFlight = false;
          }
          if (this.onMetricsUpdate) {
            this.onMetricsUpdate(data);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          this.isFrameInFlight = false;
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isFrameInFlight = false;
      };

      this.ws.onclose = () => {
        console.log('WebSocket connection closed.');
        this.isConnected = false;
        this.isFrameInFlight = false;
        clearInterval(this.pingTimer);

        if (!this.isClosedManually) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = setTimeout(() => {
            if (!this.isClosedManually) {
              this.connect();
            }
          }, 1000);
        }
      };
    } catch (e) {
      console.error('Failed to initialize WebSocket:', e);
    }
  }

  sendFrame(base64Image) {
    const now = Date.now();
    // Watchdog: If previous frame has been in-flight for > 300ms, unlock to prevent static freezing
    if (this.isFrameInFlight && (now - this.lastFrameSentTime > 300)) {
      this.isFrameInFlight = false;
    }

    if (this.ws && this.ws.readyState === WebSocket.OPEN && !this.isFrameInFlight) {
      this.isFrameInFlight = true;
      this.lastFrameSentTime = now;
      this.ws.send(JSON.stringify({
        type: 'frame',
        image: base64Image
      }));
    }
  }

  sendAudioChunk(base64Audio) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'audio',
        audio: base64Audio
      }));
    }
  }

  disconnect() {
    this.isClosedManually = true;
    clearTimeout(this.reconnectTimer);
    clearInterval(this.pingTimer);
    if (this.ws) {
      try {
        if (this.ws.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ type: 'disconnect' }));
        }
        this.ws.close();
      } catch (e) {}
      this.ws = null;
      this.isConnected = false;
      this.isFrameInFlight = false;
    }
  }
}
