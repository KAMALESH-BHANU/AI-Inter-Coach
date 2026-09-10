export class InterviewWebSocketService {
  constructor(sessionId, onMetricsUpdate) {
    this.sessionId = sessionId;
    this.onMetricsUpdate = onMetricsUpdate;
    this.ws = null;
    this.isConnected = false;
  }

  connect() {
    const wsUrl = `ws://localhost:8000/ws/interview/${this.sessionId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket connected for session:', this.sessionId);
      this.isConnected = true;
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (this.onMetricsUpdate) {
          this.onMetricsUpdate(data);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.isConnected = false;
    };

    this.ws.onclose = () => {
      console.log('WebSocket connection closed.');
      this.isConnected = false;
    };
  }

  sendFrame(base64Image) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
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
    if (this.ws) {
      this.ws.close();
      this.ws = null;
      this.isConnected = false;
    }
  }
}
