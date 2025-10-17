import sounddevice as sd
import soundfile as sf
import whisper
import os

def record_audio(duration=3, filename="audio.wav"):
    fs = 16000
    print("Recording...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write(filename, audio, fs)
    return filename

def transcribe_audio(filename="test.wav", use_mic=False, duration=3):
    """
    use_mic=False: mevcut ses dosyasını kullanır.
    use_mic=True: mikrofonla kayıt (isteğe bağlı, 2. haftada etkinleştirilecek).
    """
    # 1. Hafta: mikrofon kapalı, hazır test dosyası kullanıyoruz.
    if not os.path.exists(filename):
        print("⚠️  'test.wav' bulunamadı. Boş test örneği oluşturulacak.")
        import numpy as np, soundfile as sf
        dummy = np.zeros((16000 * duration, 1))  # 3 sn sessiz WAV
        sf.write(filename, dummy, 16000)

    # CPU modunda model yükle
    model = whisper.load_model("base", device="cpu")
    result = model.transcribe(filename, language="turkish", fp16=False)
    text = result.get("text", "").strip()
    print(f"🟩 Transcribed Text: {text if text else '[empty]'}")
    return text or "[empty]"