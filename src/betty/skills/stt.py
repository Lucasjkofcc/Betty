from math import gcd
import json
import os
from pathlib import Path
import re
import threading
import warnings

import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from scipy.signal import resample_poly
import whisper


SAMPLE_RATE = 16_000
WAKE_WORD_GRAMMAR = ["betty", "beti", "bete"]
WAKE_WORD_BLOCK_SIZE = 1_600
COMMAND_START_TIMEOUT = 4
COMMAND_MAX_DURATION = 10
COMMAND_END_SILENCE = 0.8
VAD_RMS_THRESHOLD = 120
WHISPER_INITIAL_PROMPT = (
    "Betty. Comandos em português brasileiro: que horas são, "
    "próxima música, pausa a música."
)

warnings.filterwarnings("ignore", category=UserWarning, module="whisper")

_model = None
_wake_word_model = None
_microphone_lock = threading.Lock()


class WakeWordConfigurationError(RuntimeError):
    pass


class MicrophoneError(RuntimeError):
    pass


class TranscriptionError(RuntimeError):
    pass


def get_model():
    global _model
    if _model is None:
        model_name = os.getenv("BETTY_WHISPER_MODEL", "small")
        try:
            _model = whisper.load_model(model_name, device="cpu")
        except (OSError, RuntimeError) as error:
            raise TranscriptionError(
                f"Não foi possível carregar o modelo Whisper '{model_name}': {error}"
            ) from error
    return _model


def transcribe_audio(audio, sample_rate=SAMPLE_RATE):
    """Transcreve áudio mono em português usando o Whisper local."""
    if sample_rate <= 0:
        raise ValueError("A taxa de amostragem deve ser maior que zero.")

    samples = np.asarray(audio)
    if np.issubdtype(samples.dtype, np.integer):
        samples = samples.astype(np.float32) / max(
            abs(np.iinfo(samples.dtype).min),
            np.iinfo(samples.dtype).max,
        )
    else:
        samples = samples.astype(np.float32, copy=False)

    if samples.ndim > 1:
        samples = samples.mean(axis=1)

    if samples.size == 0 or not np.any(samples):
        return ""

    if sample_rate != SAMPLE_RATE:
        divisor = gcd(sample_rate, SAMPLE_RATE)
        samples = resample_poly(
            samples,
            SAMPLE_RATE // divisor,
            sample_rate // divisor,
        ).astype(np.float32, copy=False)

    try:
        result = get_model().transcribe(
            samples,
            fp16=False,
            language="pt",
            temperature=0,
            condition_on_previous_text=False,
            initial_prompt=WHISPER_INITIAL_PROMPT,
        )
    except (OSError, RuntimeError, ValueError) as error:
        raise TranscriptionError(f"Falha ao transcrever o áudio: {error}") from error

    return result["text"].strip()


def listen(filename="input.wav", duration=5, fs=SAMPLE_RATE):
    """Grava uma entrada curta e a transcreve com o Whisper."""
    if duration <= 0:
        raise ValueError("A duração da gravação deve ser maior que zero.")
    if fs <= 0:
        raise ValueError("A taxa de amostragem deve ser maior que zero.")

    try:
        with _microphone_lock:
            recording = sd.rec(
                int(duration * fs),
                samplerate=fs,
                channels=1,
                dtype="int16",
            )
            sd.wait()
    except sd.PortAudioError as error:
        raise MicrophoneError(f"Falha ao gravar pelo microfone: {error}") from error

    wavfile.write(filename, fs, recording)
    return transcribe_audio(recording, sample_rate=fs)


def _get_wake_word_model():
    global _wake_word_model
    if _wake_word_model is not None:
        return _wake_word_model

    model_path = Path(
        os.getenv(
            "BETTY_VOSK_MODEL",
            "models/vosk-model-small-pt-0.3",
        )
    )
    if not model_path.is_absolute():
        model_path = Path(__file__).resolve().parents[3] / model_path
    if not model_path.is_dir():
        raise WakeWordConfigurationError(
            "Modelo offline do Vosk não encontrado em "
            f"'{model_path}'. Baixe e extraia vosk-model-small-pt-0.3 "
            "ou configure BETTY_VOSK_MODEL."
        )

    try:
        from vosk import Model

        _wake_word_model = Model(str(model_path))
    except ImportError as error:
        raise WakeWordConfigurationError(
            "A dependência Vosk não está instalada. Execute 'uv sync' "
            "na raiz do projeto."
        ) from error
    except Exception as error:
        raise WakeWordConfigurationError(
            f"Não foi possível carregar o modelo local do Vosk em "
            f"'{model_path}': {error}"
        ) from error
    return _wake_word_model


def _create_wake_word_recognizer():
    import vosk

    model = _get_wake_word_model()
    try:
        return vosk.KaldiRecognizer(
            model,
            SAMPLE_RATE,
            json.dumps(WAKE_WORD_GRAMMAR),
        )
    except Exception as error:
        raise WakeWordConfigurationError(
            f"Não foi possível iniciar o reconhecedor local do Vosk: {error}"
        ) from error


def _rms(samples):
    values = samples.astype(np.float32)
    return float(np.sqrt(np.mean(values * values)))


def _capture_command(
    stream,
    wake_frame,
    stop_event=None,
    should_pause=None,
):
    frames = [wake_frame]
    frame_duration = WAKE_WORD_BLOCK_SIZE / SAMPLE_RATE
    frames_to_end = max(1, round(COMMAND_END_SILENCE / frame_duration))
    max_frames = round(COMMAND_MAX_DURATION * SAMPLE_RATE / WAKE_WORD_BLOCK_SIZE)
    quiet_frames = 0
    speech_detected = False

    for _ in range(round(COMMAND_START_TIMEOUT / frame_duration)):
        try:
            recording, overflowed = stream.read(WAKE_WORD_BLOCK_SIZE)
        except sd.PortAudioError as error:
            raise MicrophoneError(
                f"Falha ao capturar o comando pelo microfone: {error}"
            ) from error

        if stop_event is not None and stop_event.is_set():
            return None
        if should_pause is not None and should_pause():
            return None

        if overflowed:
            print("[Betty] Aviso: o microfone perdeu um bloco de áudio.")

        frame = np.asarray(recording, dtype=np.int16).reshape(-1)
        if _rms(frame) >= VAD_RMS_THRESHOLD:
            frames.append(frame)
            speech_detected = True
            break

    if not speech_detected:
        return None

    for _ in range(max_frames):
        try:
            recording, overflowed = stream.read(WAKE_WORD_BLOCK_SIZE)
        except sd.PortAudioError as error:
            raise MicrophoneError(
                f"Falha ao capturar o comando pelo microfone: {error}"
            ) from error

        if stop_event is not None and stop_event.is_set():
            return None
        if should_pause is not None and should_pause():
            return None

        if overflowed:
            print("[Betty] Aviso: o microfone perdeu um bloco de áudio.")

        frame = np.asarray(recording, dtype=np.int16).reshape(-1)
        frames.append(frame)
        if _rms(frame) < VAD_RMS_THRESHOLD:
            if speech_detected:
                quiet_frames += 1
            if speech_detected and quiet_frames >= frames_to_end:
                break
        else:
            speech_detected = True
            quiet_frames = 0

    if not speech_detected:
        return None

    return np.concatenate(frames)


def _remove_wake_word(text):
    return re.sub(
        r"^\s*(?:betty|beti|bety|bete|batch)\b[\s,.:;!?-]*",
        "",
        text,
        count=1,
        flags=re.IGNORECASE,
    ).strip()


def listen_for_command(stop_event=None, should_pause=None):
    """Aguarda Betty localmente e transcreve apenas o comando com o Whisper."""
    recognizer = _create_wake_word_recognizer()
    command_audio = None

    try:
        with _microphone_lock:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=WAKE_WORD_BLOCK_SIZE,
            ) as stream:
                print(
                    '[Betty] Aguardando a palavra de ativação "Betty" '
                    "com reconhecimento local..."
                )
                while True:
                    recording, overflowed = stream.read(WAKE_WORD_BLOCK_SIZE)
                    if overflowed:
                        print("[Betty] Aviso: o microfone perdeu um bloco de áudio.")

                    frame = np.asarray(recording, dtype=np.int16).reshape(-1)
                    if stop_event is not None and stop_event.is_set():
                        return ""
                    if should_pause is not None and should_pause():
                        recognizer.Reset()
                        continue

                    try:
                        if recognizer.AcceptWaveform(frame.tobytes()):
                            result = json.loads(recognizer.Result())
                            detected_text = result.get("text", "")
                        else:
                            partial = json.loads(recognizer.PartialResult())
                            detected_text = partial.get("partial", "")
                    except Exception as error:
                        raise WakeWordConfigurationError(
                            f"Falha no reconhecimento local do wake word: {error}"
                        ) from error

                    if _contains_wake_word(detected_text):
                        command_audio = _capture_command(
                            stream,
                            frame,
                            stop_event=stop_event,
                            should_pause=should_pause,
                        )
                        break
    except sd.PortAudioError as error:
        raise MicrophoneError(
            f"Não foi possível acessar o microfone: {error}"
        ) from error

    if command_audio is None:
        return ""

    try:
        text = transcribe_audio(
            command_audio,
            sample_rate=SAMPLE_RATE,
        )
    except TranscriptionError as error:
        print(f"[Betty] {error}")
        return ""
    return _remove_wake_word(text)


def _contains_wake_word(text):
    words = set(re.findall(r"[a-z]+", text.casefold()))
    return bool(words.intersection({"betty", "beti", "bety", "bete"}))
