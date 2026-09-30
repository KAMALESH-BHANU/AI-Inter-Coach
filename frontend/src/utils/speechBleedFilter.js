/**
 * Utility to eliminate AI Question audio echo/bleed from candidate speech transcripts.
 * Strips out any accidental microphone captures of the AI's question text.
 */

function cleanWords(text) {
  return (text || '')
    .toLowerCase()
    .replace(/[{}\[\]()<>;=+\-*\/%&|^!~?.,:;"'`_#]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Removes any AI question echo/bleed that may have been captured at the beginning of the candidate's speech.
 * 
 * @param {string} rawTranscript The candidate's raw transcript
 * @param {string} questionText The AI question text
 * @returns {string} Sanitized transcript with question echo removed
 */
export function stripQuestionEcho(rawTranscript, questionText) {
  if (!rawTranscript || !questionText) return rawTranscript || '';

  const cleanTrans = cleanWords(rawTranscript);
  const cleanQ = cleanWords(questionText);

  if (!cleanTrans || !cleanQ) return rawTranscript;

  const qWords = cleanQ.split(' ').filter(Boolean);
  const transWords = cleanTrans.split(' ').filter(Boolean);

  if (qWords.length === 0 || transWords.length === 0) return rawTranscript;

  // 1. Check if the entire transcript is a substring of the question
  if (cleanQ.includes(cleanTrans)) {
    // The entire captured transcript was just words from the question!
    return '';
  }

  // 2. Check for question tail bleed at the beginning of the candidate's transcript
  // Test phrase lengths from max to min 2 words
  let matchWordCount = 0;

  for (let len = Math.min(transWords.length, qWords.length, 12); len >= 2; len--) {
    const candidatePrefix = transWords.slice(0, len).join(' ');
    
    // Check if this prefix exists anywhere in the question text (especially near the end)
    if (cleanQ.includes(candidatePrefix)) {
      matchWordCount = len;
      break;
    }
  }

  if (matchWordCount > 0) {
    // Strip the matching words from the start of the original transcript
    const rawTokens = rawTranscript.trim().split(/\s+/);
    if (matchWordCount >= rawTokens.length) {
      return '';
    }
    const sanitized = rawTokens.slice(matchWordCount).join(' ').trim();
    // Clean leading punctuation if any left
    return sanitized.replace(/^[,.\-!?:;"'\s]+/, '').trim();
  }

  return rawTranscript.trim();
}
