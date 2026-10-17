import sounddevice as sd
from scipy.io import wavfile
import whisper
import os
import warnings

# Suprime aviso de inferência na CPU
warnings.filterwarnings("ignore", category=UserWarning, module="whisper")

# Inicializa o modelo como None
_model = None

def get_model():
    global _model
    if _model is None:
        _model = whisper.load_model("base", device="cpu")
    return _model

def listen(filename="input.wav", duration=5, fs=44100):
    """Grava áudio e transcreve usando Whisper."""
    model = get_model()

    # Grava áudio
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    # Salva em WAV
    wavfile.write(filename, fs, recording)

    # Transcreve
    result = model.transcribe(filename, fp16=False)

    return result["text"].strip()
