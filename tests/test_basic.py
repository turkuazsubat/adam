from stt import record_audio
from nlu import interpret_text
import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_record_audio():
    assert record_audio(duration=1) == "audio.wav"

def test_nlu():
    assert interpret_text("hesap makinesini aç") == "open_calculator"




