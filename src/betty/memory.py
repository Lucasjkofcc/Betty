import json
from pathlib import Path


MEMORY_FILE = Path("memory.json")


def load_memory():
    if not MEMORY_FILE.exists():
        return {}

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_memory(key, value):
    memory = load_memory()
    memory[key] = value

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=4)


def get_memory(key):
    memory = load_memory()
    return memory.get(key)
