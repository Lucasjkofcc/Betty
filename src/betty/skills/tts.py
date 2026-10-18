import sys
import re
import queue
import threading
import subprocess
import tempfile
import os

import numpy as np
import soundfile as sf
from kokoro import KPipeline
import warnings
import logging

from .media import pausar_temporario, retomar_temporario
os.environ["PYTHONWARNINGS"] = "ignore"

VOICE = "pf_dora"
SAMPLE_RATE = 24000
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
audio_queue = queue.Queue()
is_speaking = threading.Event()

warnings.filterwarnings("ignore")
# Carrega o modelo uma vez, usando a CPU.
pipeline = KPipeline(
    lang_code="p",
    repo_id="hexgrad/Kokoro-82M",
    device="cpu",
)


def clean_text(text: str) -> str:
    """Remove códigos ANSI e caracteres de controle."""
    text = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)
    text = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    """Divide o texto preservando a pontuação."""
    return [
        part.strip()
        for part in re.findall(r"[^.!?,…]+(?:\.{3}|[.!?,…]+|$)", text)
        if part.strip()
    ]


def silence(seconds: float) -> np.ndarray:
    """Gera silêncio para inserir entre frases."""
    frames = int(SAMPLE_RATE * seconds)
    return np.zeros(frames, dtype=np.float32)


def generate_audio(text: str) -> np.ndarray:
    """Gera áudio com Kokoro em português brasileiro."""
    parts = []

    for _, _, audio in pipeline(text, voice=VOICE, speed=1):
        if hasattr(audio, "cpu"):
            audio = audio.cpu().numpy()

        parts.append(np.asarray(audio, dtype=np.float32).reshape(-1))

    if not parts:
        return np.array([], dtype=np.float32)

    return np.concatenate(parts)


def play_audio(file_path: str):
    """EU ODEIO O WINDOWS"""
    if sys.platform.startswith("win"):
        import sounddevice as sd

        audio, sample_rate = sf.read(
            file_path,
            dtype="float32",
        )

        sd.play(audio, sample_rate)
        sd.wait()

    else:
        subprocess.run(["aplay", "-q", file_path], check=True)

def audio_worker():
    while True:
        item = audio_queue.get()

        try:
            if item is None:
                return

            text, output_path = item

            chunks = split_sentences(text)
            audio_parts = []

            pauses = {
                ",": 0.15,
                ".": 0.45,
                "!": 0.50,
                "?": 0.50,
                "...": 0.80,
                "…": 0.80,
            }

            # Primeiro, gera TODO o áudio sem interromper a música.
            for chunk in chunks:
                audio = generate_audio(chunk)

                if audio.size == 0:
                    continue

                audio_parts.append(audio)

                punctuation = next(
                    (
                        mark
                        for mark in ("...", "…", ",", ".", "!", "?")
                        if chunk.endswith(mark)
                    ),
                    "",
                )

                pause = pauses.get(punctuation, 0.0)

                if pause:
                    audio_parts.append(silence(pause))

            if not audio_parts:
                continue

            final_audio = np.concatenate(audio_parts)

            # Prepara o WAV antes de pausar qualquer música.
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False,
            ) as temp:
                temp_path = temp.name

            try:
                sf.write(
                    temp_path,
                    final_audio,
                    SAMPLE_RATE,
                    subtype="PCM_16",
                )

                # Só agora a Betty está pronta para falar.
                pausar_temporario()
                is_speaking.set()

                try:
                    play_audio(temp_path)
                finally:
                    # Retoma somente depois que a fala terminar.
                    retomar_temporario()
                    is_speaking.clear()

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            print(f"Error in audio worker: {e}")

        finally:
            is_speaking.clear()
            audio_queue.task_done()


threading.Thread(
    target=audio_worker,
    daemon=True,
).start()


def speak(
    text: str,
    model_path=None,
    output_path: str = "output.wav",
):
    """Enfileira uma fala para o Kokoro."""
    text = clean_text(text)

    if not text:
        return

    # model_path permanece por compatibilidade com chamadas antigas.
    audio_queue.put((text, output_path))
