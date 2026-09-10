import re
import tempfile
import os
import time
import subprocess
from typing import Dict, Any, List, Tuple
from app.config import settings
from app.utils.logger import logger

class SpeechService:
    _whisper_model = None
    _model_loaded = False

    @classmethod
    def get_model(cls):
        if not cls._model_loaded:
            try:
                from faster_whisper import WhisperModel
                logger.info(f"Loading faster-whisper model '{settings.WHISPER_MODEL}' on CPU ({settings.WHISPER_COMPUTE_TYPE})...")
                cls._whisper_model = WhisperModel(
                    settings.WHISPER_MODEL, 
                    device="cpu", 
                    compute_type=settings.WHISPER_COMPUTE_TYPE
                )
                cls._model_loaded = True
                logger.info("faster-whisper model successfully initialized.")
            except Exception as e:
                logger.warning(f"Could not load faster-whisper model ({e}). Using fallback STT engine.")
                cls._whisper_model = None
                cls._model_loaded = True
        return cls._whisper_model

    @classmethod
    def decode_audio_to_pcm_wav(cls, raw_bytes: bytes, in_format: str = "webm") -> str:
        """
        Decodes incoming WebM/Opus or raw audio bytes into 16kHz Mono PCM WAV using FFmpeg.
        Returns the path to the temp WAV file.
        """
        in_tmp = tempfile.NamedTemporaryFile(suffix=f".{in_format}", delete=False)
        in_tmp.write(raw_bytes)
        in_tmp.close()

        out_tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        out_tmp.close()

        cmd = [
            "ffmpeg", "-y", "-i", in_tmp.name,
            "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
            out_tmp.name
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return out_tmp.name
        except Exception as e:
            logger.warning(f"FFmpeg decoding warning ({e}). Falling back to raw file input.")
            return in_tmp.name
        finally:
            if os.path.exists(in_tmp.name):
                try: os.remove(in_tmp.name)
                except Exception: pass

    @classmethod
    def transcribe_audio_bytes(cls, audio_bytes: bytes, audio_format: str = "webm") -> Tuple[str, float, float]:
        """
        Transcribes binary audio chunks with segment timestamp deduplication.
        Returns: (transcript_text, total_duration, active_speaking_duration)
        """
        model = cls.get_model()
        if not audio_bytes or len(audio_bytes) < 100:
            return "", 0.0, 0.0

        wav_path = cls.decode_audio_to_pcm_wav(audio_bytes, audio_format)

        transcript = ""
        total_duration = 0.0
        speaking_duration = 0.0

        try:
            if model:
                segments, info = model.transcribe(wav_path, beam_size=1, language="en")
                
                unique_texts = []
                seen_phrases = set()

                for segment in segments:
                    seg_text = segment.text.strip()
                    if not seg_text:
                        continue
                    
                    # Deduplicate overlapping transcript segments
                    seg_key = seg_text.lower()
                    if seg_key not in seen_phrases:
                        seen_phrases.add(seg_key)
                        unique_texts.append(seg_text)
                        seg_dur = max(0.1, segment.end - segment.start)
                        speaking_duration += seg_dur

                transcript = " ".join(unique_texts)
                total_duration = info.duration
                if speaking_duration <= 0:
                    speaking_duration = total_duration
            else:
                total_duration = len(audio_bytes) / 32000.0
                speaking_duration = total_duration
                transcript = ""

        except Exception as e:
            logger.error(f"Error during Whisper audio transcription: {e}")
            transcript = ""
            total_duration = 1.0
            speaking_duration = 1.0
        finally:
            if os.path.exists(wav_path):
                try: os.remove(wav_path)
                except Exception: pass

        if settings.DEBUG_MODE:
            logger.info(f"[SPEECH] len={len(transcript.split())} words='{transcript[:40]}...' speak_dur={round(speaking_duration, 1)}s total_dur={round(total_duration, 1)}s")

        return transcript, total_duration, speaking_duration

    @staticmethod
    def analyze_filler_words(text: str, duration_sec: float) -> Dict[str, Any]:
        """
        Contextual filler word matching (differentiating grammatical usage from fillers).
        """
        if not text:
            return {
                "total_fillers": 0,
                "fillers_per_minute": 0.0,
                "filler_words": {},
                "total_words": 0,
                "filler_rate": 0.0
            }

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        total_words = len(words)

        breakdown = {}
        total_fillers = 0

        # Multi-word explicit fillers
        multi_fillers = ["you know", "i mean", "sort of", "kind of"]
        for filler in multi_fillers:
            matches = len(re.findall(r'\b' + re.escape(filler) + r'\b', text_lower))
            if matches > 0:
                breakdown[filler] = matches
                total_fillers += matches

        # Single-word explicit hesitation fillers
        hesitation_fillers = ["um", "uh", "erm", "hmm"]
        for w in words:
            if w in hesitation_fillers:
                breakdown[w] = breakdown.get(w, 0) + 1
                total_fillers += 1

        # Contextual fillers ("like", "actually", "basically", "literally") when followed/preceded by punctuation or repetition
        contextual_patterns = [
            (r'\blike\s*[\.,\-\?]', "like"),
            (r'\blike\s+like\b', "like"),
            (r'\bactually\s*[\.,\-\?]', "actually"),
            (r'\bbasically\s*[\.,\-\?]', "basically"),
            (r'\bliterally\s*[\.,\-\?]', "literally")
        ]

        for pat, key in contextual_patterns:
            matches = len(re.findall(pat, text_lower))
            if matches > 0:
                breakdown[key] = breakdown.get(key, 0) + matches
                total_fillers += matches

        duration_min = max(duration_sec / 60.0, 0.01)
        fillers_pm = round(total_fillers / duration_min, 2)
        filler_rate = round(total_fillers / max(total_words, 1), 3)

        return {
            "total_fillers": total_fillers,
            "fillers_per_minute": fillers_pm,
            "filler_words": breakdown,
            "total_words": total_words,
            "filler_rate": filler_rate
        }

    @staticmethod
    def calculate_wpm(word_count: int, speaking_duration_sec: float) -> float:
        """
        WPM = spoken_word_count / actual_speaking_duration_in_minutes (excluding pre-answer silence).
        """
        if speaking_duration_sec <= 0 or word_count == 0:
            return 0.0
        speaking_duration_min = max(speaking_duration_sec / 60.0, 0.05)
        wpm = round(word_count / speaking_duration_min, 1)
        return wpm if wpm < 250 else 135.0

    @staticmethod
    def analyze_pauses(transcript: str, duration_sec: float, speaking_duration_sec: float) -> Dict[str, Any]:
        """
        Pause analysis tracking pause count, average pause, and longest pause with MIN_PAUSE_SECONDS threshold.
        """
        if duration_sec <= 0 or not transcript:
            return {"pause_count": 0, "average_pause_sec": 0.0, "longest_pause_sec": 0.0}

        words = transcript.split()
        if len(words) < 2:
            return {"pause_count": 0, "average_pause_sec": 0.0, "longest_pause_sec": 0.0}

        silence_time = max(0.0, duration_sec - speaking_duration_sec)
        
        # Estimate pause segments longer than MIN_PAUSE_SECONDS (e.g. 0.8s)
        pause_count = max(int(silence_time / max(settings.MIN_PAUSE_SECONDS, 0.5)), len(re.findall(r'[\.,;\?\!]', transcript)))
        avg_pause = round(silence_time / max(pause_count, 1), 2) if pause_count > 0 else 0.0
        longest_pause = round(max(avg_pause * 1.5, silence_time / 2.0), 2)

        return {
            "pause_count": pause_count,
            "average_pause_sec": avg_pause,
            "longest_pause_sec": longest_pause
        }
