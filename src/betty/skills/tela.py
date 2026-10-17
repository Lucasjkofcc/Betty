import os
import subprocess
import tempfile
import ollama


def screenshot():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as image:
        path = image.name

    try:
        subprocess.run(["grim", path], check=True)
    except Exception:
        os.remove(path)
        raise

    return path


def ocr():
    path = screenshot()

    try:
        result = subprocess.run(
            ["tesseract", path, "stdout", "-l", "por"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    finally:
        if os.path.exists(path):
            os.remove(path)


def analyze_screen():
    path = screenshot()

    try:
        result = ollama.chat(
            model="moondream:latest",
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Descreva objetivamente o que está visível "
                        "na captura de tela. Identifique aplicativos, "
                        "jogos e atividades. Não invente detalhes."
                    ),
                    "images": [path],
                }
            ],
        )
        print(repr(result))
        return result["message"]["content"].strip()
    finally:
        subprocess.Popen(["ollama", "stop", "moondream:latest"])
        if os.path.exists(path):
            os.remove(path)
