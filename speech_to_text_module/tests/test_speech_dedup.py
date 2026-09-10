import pytest
from app.services.speech_service import SpeechService

def test_contextual_filler_word_matching():
    # "I like Java" should not count as a filler
    text_normal = "I like Java because it is object oriented and actually robust"
    fillers_normal = SpeechService.analyze_filler_words(text_normal, 15.0)
    assert fillers_normal["total_fillers"] <= 1

    # Hesitation fillers "um, uh, like..." should count as fillers
    text_filler = "Um, uh, I think, like... basically, you know, Java is nice"
    fillers = SpeechService.analyze_filler_words(text_filler, 15.0)
    assert fillers["total_fillers"] >= 3
    assert fillers["filler_rate"] > 0.0

def test_actual_speech_wpm_calculation():
    # 100 words spoken in 45 seconds (0.75 min) of actual speech duration
    word_count = 100
    speaking_dur = 45.0
    wpm = SpeechService.calculate_wpm(word_count, speaking_dur)
    
    # 100 / 0.75 = 133.3 WPM
    assert 130.0 <= wpm <= 135.0

def test_pause_analysis():
    transcript = "I know Java. I have worked with Spring Boot."
    pauses = SpeechService.analyze_pauses(transcript, duration_sec=30.0, speaking_duration_sec=20.0)
    
    assert "pause_count" in pauses
    assert "average_pause_sec" in pauses
    assert pauses["average_pause_sec"] >= 0.0
