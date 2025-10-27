from stt import record_audio
from nlu import interpret_text
import sys, os
from response import generate_response

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_record_audio():
    assert record_audio(duration=1) == "audio.wav"

def test_nlu():
    assert interpret_text("hesap makinesini aç") == "open_calculator"
#Week2
def test_generate_response_basic():
    reply = generate_response("Roma tarihi nedir?")
    assert isinstance(reply, str)
    assert len(reply) > 0
    
def test_generate_response_basic():
    reply = generate_response("Roma İmparatorluğu nedir?")
    assert isinstance(reply, str)
    assert len(reply) > 0

def test_log_and_db_created():
    assert os.path.exists("project.log")
    assert os.path.exists("db/project.db")

