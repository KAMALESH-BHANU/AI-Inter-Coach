/**
 * AI Interview Coach — Reusable Browser Text-to-Speech (TTS) Utility
 * 
 * Provides robust Web Speech API management with:
 * - Female English voice prioritization
 * - Async voice loading & 'voiceschanged' event subscription
 * - Chromium stalled audio context unsticking
 * - Detailed [TTS] lifecycle logging
 * - Text extraction for general, pseudocode, and SQL interview questions
 */

const VOICE_STORAGE_KEY = 'ai_interview_coach_tts_voice_uri';

// In-memory reference to the currently active utterance
let activeUtterance = null;
let lastSpeechInfo = {
  text: '',
  voiceName: '',
  startedAt: null,
  completedAt: null,
  lastError: null,
  state: 'IDLE' // IDLE | SPEAKING | PAUSED | FINISHED | ERROR
};

/**
 * Safely extracts human-readable text from any question format (technical, pseudocode, SQL).
 * @param {Object|string} question 
 * @returns {string} Clean text suitable for voice reading
 */
export function getReadableQuestionText(question) {
  if (!question) return '';

  let rawText = '';

  if (typeof question === 'string') {
    rawText = question.trim();
  } else if (question.type === 'sql') {
    const title = question.title ? `${question.title}. ` : '';
    const desc = question.description || question.question || '';
    rawText = `${title}${desc}`.trim();
  } else {
    // Standard or pseudocode question
    const primaryText = question.question || question.text || question.description || question.title || '';
    if (primaryText.includes('\n\n')) {
      const parts = primaryText.split('\n\n');
      rawText = `${parts[0].trim()}. Please review the code snippet on screen and select the correct option.`;
    } else if (question.code_snippet) {
      rawText = `${primaryText.trim()}. Please review the code snippet on screen and select the correct option.`;
    } else {
      rawText = primaryText.trim();
    }
  }

  // Clean markdown backticks, code blocks, syntax symbols, or asterisks for clear pronunciation
  return String(rawText ?? '')
    .replace(/```[\s\S]*?```/g, ' [Code snippet displayed on screen] ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/[{}\[\]()<>;=+\-*\/%&|^!~]/g, ' ')
    .replace(/[*_#]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Checks if browser speech synthesis is supported.
 * @returns {boolean}
 */
export function isTtsSupported() {
  return typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
}

/**
 * Finds a reliable local/offline English voice to guarantee playback if an online voice fails.
 * @param {SpeechSynthesisVoice[]} availableVoices 
 * @returns {SpeechSynthesisVoice|null}
 */
export function findFallbackLocalVoice(availableVoices) {
  if (!availableVoices || availableVoices.length === 0) return null;

  const englishVoices = availableVoices.filter(
    v => v.lang && v.lang.toLowerCase().startsWith('en')
  );
  const pool = englishVoices.length > 0 ? englishVoices : availableVoices;

  const localKeywords = [
    'microsoft zira desktop',
    'microsoft zira',
    'google us english',
    'microsoft david desktop',
    'microsoft david',
    'samantha',
    'victoria',
    'karen',
    'tessa'
  ];

  for (const kw of localKeywords) {
    const match = pool.find(v => v.name.toLowerCase().includes(kw));
    if (match) return match;
  }

  // Any voice without 'online' in its name
  const offlineVoice = pool.find(v => !v.name.toLowerCase().includes('online'));
  if (offlineVoice) return offlineVoice;

  return pool[0] || null;
}

/**
 * Finds the highest quality English female voice available in the browser.
 * Priority:
 * 1. Known Natural/Neural Female English Voices or Local Voices
 * 2. Any voice tagged 'female', 'woman', or 'girl'
 * 3. Any natural/neural English voice
 * 4. Any English voice (en-US, en-GB, etc.)
 * 5. System default voice
 * 
 * @param {SpeechSynthesisVoice[]} availableVoices 
 * @returns {SpeechSynthesisVoice|null}
 */
export function findBestFemaleVoice(availableVoices) {
  if (!availableVoices || availableVoices.length === 0) return null;

  const englishVoices = availableVoices.filter(
    v => v.lang && v.lang.toLowerCase().startsWith('en')
  );
  const candidatePool = englishVoices.length > 0 ? englishVoices : availableVoices;

  // 1. Known high-quality female English voices on Windows, macOS, Chrome, Edge, Android
  const preferredFemaleKeywords = [
    'microsoft zira desktop',
    'microsoft zira',
    'microsoft jenny online (natural)',
    'microsoft jenny',
    'microsoft aria online (natural)',
    'microsoft aria',
    'google us english',
    'microsoft libby online (natural)',
    'microsoft libby',
    'microsoft sonia online (natural)',
    'microsoft sonia',
    'microsoft natasha online (natural)',
    'microsoft natasha',
    'microsoft neerja online (natural)',
    'microsoft neerja',
    'samantha',
    'victoria',
    'karen',
    'fiona',
    'moira',
    'tessa',
    'veena'
  ];

  for (const keyword of preferredFemaleKeywords) {
    const match = candidatePool.find(v => v.name.toLowerCase().includes(keyword));
    if (match) return match;
  }

  // 2. Any voice explicitly containing female/woman/girl in name
  const taggedFemale = candidatePool.find(v => {
    const n = v.name.toLowerCase();
    return n.includes('female') || n.includes('woman') || n.includes('girl');
  });
  if (taggedFemale) return taggedFemale;

  // 3. Any natural or neural English voice
  const naturalVoice = candidatePool.find(v => {
    const n = v.name.toLowerCase();
    return n.includes('natural') || n.includes('neural') || n.includes('online');
  });
  if (naturalVoice) return naturalVoice;

  // 4. Any en-US voice
  const enUsVoice = candidatePool.find(v => v.lang.toLowerCase() === 'en-us');
  if (enUsVoice) return enUsVoice;

  // 5. Any English voice
  if (englishVoices.length > 0) return englishVoices[0];

  // 6. Fallback to first available voice
  return availableVoices[0] || null;
}

/**
 * Returns the list of currently available browser voices.
 * @returns {SpeechSynthesisVoice[]}
 */
export function getAvailableVoices() {
  if (!isTtsSupported()) return [];
  try {
    return window.speechSynthesis.getVoices() || [];
  } catch (e) {
    console.error('[TTS] Error getting voices:', e);
    return [];
  }
}

/**
 * Subscribes to the browser's 'voiceschanged' event with automatic cleanup.
 * @param {Function} callback Callback receiving the list of voices
 * @returns {Function} Unsubscribe function
 */
export function subscribeToVoices(callback) {
  if (!isTtsSupported()) return () => {};

  const handleVoices = () => {
    const voices = getAvailableVoices();
    console.log('[TTS] Available voices loaded:', voices.length);
    if (callback) callback(voices);
  };

  // Immediate check
  const initialVoices = getAvailableVoices();
  if (initialVoices.length > 0) {
    if (callback) callback(initialVoices);
  }

  // Listen for dynamic voice loading
  window.speechSynthesis.addEventListener('voiceschanged', handleVoices);

  return () => {
    window.speechSynthesis.removeEventListener('voiceschanged', handleVoices);
  };
}

/**
 * Core function to speak question text aloud.
 * 
 * @param {string|Object} textOrQuestion 
 * @param {Object} options Configuration options
 * @param {string} [options.voiceUri] Specific voice URI to use
 * @param {number} [options.rate=0.95] Speaking speed rate (0.5 to 1.5)
 * @param {number} [options.pitch=1.0] Voice pitch (0.5 to 1.5)
 * @param {number} [options.volume=1.0] Audio volume (0.0 to 1.0)
 * @param {Function} [options.onStart] Callback when speech starts
 * @param {Function} [options.onEnd] Callback when speech completes
 * @param {Function} [options.onError] Callback when an error occurs
 * @returns {boolean} True if speech was initiated successfully
 */
export function speakQuestion(textOrQuestion, options = {}) {
  if (!isTtsSupported()) {
    console.error('[TTS] Browser speech synthesis is unavailable in this environment');
    lastSpeechInfo.lastError = 'Browser speech synthesis is unavailable';
    lastSpeechInfo.state = 'ERROR';
    if (options.onError) options.onError('TTS unavailable');
    return false;
  }

  const cleanText = getReadableQuestionText(textOrQuestion);

  console.log('[TTS] Current question text:', cleanText);

  if (!cleanText) {
    console.error('[TTS] Cannot speak empty question text');
    lastSpeechInfo.lastError = 'Empty question text';
    lastSpeechInfo.state = 'FINISHED';
    if (options.onEnd) options.onEnd();
    return false;
  }

  try {
    const synthesis = window.speechSynthesis;

    // Cancel previous utterance before starting a new one
    synthesis.cancel();

    // Unpause/resume Chromium speech engine in case audio context was suspended
    if (synthesis.paused) {
      synthesis.resume();
    }

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = options.lang || 'en-US';
    utterance.rate = options.rate !== undefined ? options.rate : 1.05;
    utterance.pitch = options.pitch !== undefined ? options.pitch : 1.0;
    utterance.volume = options.volume !== undefined ? options.volume : 1.0;

    // Resolve voice selection
    const voices = getAvailableVoices();
    let selectedVoice = null;

    if (options.voiceUri) {
      selectedVoice = voices.find(v => v.voiceURI === options.voiceUri);
    }

    if (!selectedVoice) {
      const savedUri = typeof sessionStorage !== 'undefined' ? sessionStorage.getItem(VOICE_STORAGE_KEY) : null;
      if (savedUri) {
        selectedVoice = voices.find(v => v.voiceURI === savedUri);
      }
    }

    if (!selectedVoice) {
      selectedVoice = findBestFemaleVoice(voices);
      if (selectedVoice && typeof sessionStorage !== 'undefined') {
        try {
          sessionStorage.setItem(VOICE_STORAGE_KEY, selectedVoice.voiceURI);
        } catch (e) {}
      }
    }

    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    console.log('[TTS] Selected voice:', selectedVoice?.name || 'Default System Voice');

    let finished = false;
    let fallbackTimer = null;

    const cleanupAndFinish = () => {
      if (finished) return;
      finished = true;
      if (fallbackTimer) {
        clearTimeout(fallbackTimer);
        fallbackTimer = null;
      }
      activeUtterance = null;
    };

    // Calculate max expected duration for question based on word count (generous guard window)
    const wordCount = cleanText.split(/\s+/).filter(Boolean).length;
    const maxExpectedDurationMs = Math.max(12000, (wordCount / 1.4) * 1000 + 5000);

    // Lifecycle events
    utterance.onstart = () => {
      console.log('[TTS] Speech started:', cleanText);
      lastSpeechInfo.text = cleanText;
      lastSpeechInfo.voiceName = utterance.voice?.name || 'Default';
      lastSpeechInfo.startedAt = new Date().toLocaleTimeString();
      lastSpeechInfo.lastError = null;
      lastSpeechInfo.state = 'SPEAKING';
      if (options.onStart) options.onStart();

      // Guard timer ONLY in case browser completely drops onend event
      fallbackTimer = setTimeout(() => {
        if (!finished) {
          console.log('[TTS] Utterance reached maximum duration window, auto-finishing');
          cleanupAndFinish();
          lastSpeechInfo.completedAt = new Date().toLocaleTimeString();
          lastSpeechInfo.state = 'FINISHED';
          if (options.onEnd) options.onEnd();
        }
      }, maxExpectedDurationMs);
    };

    utterance.onend = () => {
      console.log('[TTS] Speech completed physically');
      cleanupAndFinish();
      lastSpeechInfo.completedAt = new Date().toLocaleTimeString();
      lastSpeechInfo.state = 'FINISHED';
      // 350ms acoustic clearance buffer to let speakers and room reverberation completely settle
      setTimeout(() => {
        if (options.onEnd) options.onEnd();
      }, 350);
    };

    utterance.onerror = (event) => {
      cleanupAndFinish();
      // Handle interruptions from cancel() or user navigation
      if (event.error === 'interrupted' || event.error === 'canceled') {
        console.log('[TTS] Speech interrupted or cancelled normally');
        lastSpeechInfo.state = 'IDLE';
        if (options.onEnd) options.onEnd();
        return;
      }
      console.error('[TTS] Speech error:', event.error, event);

      // Automatic fallback if selected voice encountered a cloud synthesis failure
      if (!options._isRetry && (event.error === 'synthesis-failed' || event.error === 'network' || event.error === 'audio-busy' || event.error === 'synthesis-unavailable')) {
        const fallbackVoice = findFallbackLocalVoice(voices);
        if (fallbackVoice && fallbackVoice.voiceURI !== selectedVoice?.voiceURI) {
          console.log('[TTS] Online voice synthesis failed. Automatically falling back to local voice:', fallbackVoice.name);
          try {
            sessionStorage.setItem(VOICE_STORAGE_KEY, fallbackVoice.voiceURI);
          } catch (e) {}

          speakQuestion(textOrQuestion, {
            ...options,
            voiceUri: fallbackVoice.voiceURI,
            _isRetry: true
          });
          return;
        }
      }

      lastSpeechInfo.lastError = event.error || 'Unknown speech error';
      lastSpeechInfo.state = 'ERROR';
      if (options.onError) options.onError(event.error);
      if (options.onEnd) options.onEnd();
    };

    activeUtterance = utterance;

    // Speak
    synthesis.speak(utterance);

    // Immediate fallback if onstart never fires (e.g. autoplay restriction)
    setTimeout(() => {
      if (!finished && lastSpeechInfo.state !== 'SPEAKING') {
        console.log('[TTS] onstart was delayed or blocked, releasing speech state');
        cleanupAndFinish();
        if (options.onEnd) options.onEnd();
      }
    }, 1500);

    console.log('[TTS] speak() called successfully', {
      textLength: cleanText.length,
      voice: utterance.voice?.name,
      language: utterance.lang,
      rate: utterance.rate
    });

    return true;
  } catch (error) {
    console.error('[TTS] Unexpected error in speakQuestion():', error);
    lastSpeechInfo.lastError = error.message;
    lastSpeechInfo.state = 'ERROR';
    if (options.onError) options.onError(error.message);
    return false;
  }
}

/**
 * Cancels any active speech synthesis.
 */
export function cancelSpeech() {
  if (!isTtsSupported()) return;
  try {
    window.speechSynthesis.cancel();
    activeUtterance = null;
    lastSpeechInfo.state = 'IDLE';
    console.log('[TTS] Speech cancelled explicitly');
  } catch (e) {
    console.error('[TTS] Error cancelling speech:', e);
  }
}

/**
 * Pauses active speech synthesis.
 */
export function pauseSpeech() {
  if (!isTtsSupported()) return;
  try {
    window.speechSynthesis.pause();
    lastSpeechInfo.state = 'PAUSED';
    console.log('[TTS] Speech paused');
  } catch (e) {
    console.error('[TTS] Error pausing speech:', e);
  }
}

/**
 * Resumes paused speech synthesis.
 */
export function resumeSpeech() {
  if (!isTtsSupported()) return;
  try {
    window.speechSynthesis.resume();
    lastSpeechInfo.state = 'SPEAKING';
    console.log('[TTS] Speech resumed');
  } catch (e) {
    console.error('[TTS] Error resuming speech:', e);
  }
}

/**
 * Returns latest debug information about TTS state.
 * @returns {Object}
 */
export function getTtsDebugInfo() {
  return {
    isSupported: isTtsSupported(),
    speaking: isTtsSupported() ? window.speechSynthesis.speaking : false,
    paused: isTtsSupported() ? window.speechSynthesis.paused : false,
    pending: isTtsSupported() ? window.speechSynthesis.pending : false,
    availableVoiceCount: getAvailableVoices().length,
    ...lastSpeechInfo
  };
}
