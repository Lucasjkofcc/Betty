import os
import subprocess
import sys
import tempfile

import ollama


def screenshot():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as image:
        path = image.name

    try:
        if sys.platform.startswith("win"):
            import mss

            with mss.MSS() as capture:
                capture.shot(output=path)
        else:
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
                        "Describe objectively what is visible in the "
                        "screenshot. Identify apps, games and activities. "
                        "Do not invent details."
                    ),
                    "images": [path],
                }
            ],
        )
        return result.message.content.strip()
    finally:
        subprocess.Popen(["ollama", "stop", "moondream:latest"])
        if os.path.exists(path):
            os.remove(path)
