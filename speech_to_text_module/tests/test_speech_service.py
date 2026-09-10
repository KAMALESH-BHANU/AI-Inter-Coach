import pytest
from app.services.speech_service import SpeechService

def test_filler_word_detection():
    sample_text = "Um, actually, I think basically Spring Boot is, uh, very useful, you know?"
    result = SpeechService.analyze_filler_words(sample_text, duration_sec=30.0)
    
    assert result["total_fillers"] >= 3
    assert "um" in result["filler_words"]
    assert "uh" in result["filler_words"]
    assert "you know" in result["filler_words"]
    assert result["fillers_per_minute"] > 0

def test_wpm_calculation():
    # 130 words spoken in 60 seconds = 130 WPM
    wpm = SpeechService.calculate_wpm(130, 60.0)
    assert wpm == 130.0

    # 60 words in 30 seconds = 120 WPM
    wpm_half = SpeechService.calculate_wpm(60, 30.0)
    assert wpm_half == 120.0

def test_pause_analysis():
    transcript = "Well, let me think. First, we initialize the database. Second, we configure security."
    pauses = SpeechService.analyze_pauses(transcript, duration_sec=20.0, speaking_duration_sec=15.0)
    assert pauses["pause_count"] >= 1
