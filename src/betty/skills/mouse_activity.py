import subprocess
import threading
import time
from datetime import datetime


POLL_INTERVAL = 2
ACTIVE_WITHIN = 5 * 60

_last_position: tuple[int, int] | None = None
_last_movement: datetime | None = None
_lock = threading.Lock()


def mouse_active_within(
    seconds: int = ACTIVE_WITHIN,
    *,
    now: datetime | None = None,
) -> bool:
    current_time = datetime.now() if now is None else now

    with _lock:
        return (
            _last_movement is not None
            and (current_time - _last_movement).total_seconds() <= seconds
        )


def monitor_mouse_activity() -> None:
    global _last_movement, _last_position

    last_error = None

    while True:
        try:
            result = subprocess.run(
                ["hyprctl", "cursorpos"],
                capture_output=True,
                text=True,
                check=True,
                timeout=3,
            )
            x_text, y_text = result.stdout.strip().split(",", maxsplit=1)
            position = (int(x_text.strip()), int(y_text.strip()))
        except FileNotFoundError as error:
            error_message = f"hyprctl não encontrado: {error}"
        except subprocess.CalledProcessError as error:
            error_message = error.stderr.strip() or str(error)
        except subprocess.TimeoutExpired as error:
            error_message = f"hyprctl excedeu o tempo limite: {error}"
        except ValueError as error:
            error_message = f"posição do cursor inválida: {error}"
        else:
            last_error = None
            current_time = datetime.now()

            with _lock:
                if _last_position is not None and position != _last_position:
                    _last_position = position
                    _last_movement = current_time
                elif _last_position is None:
                    _last_position = position

            time.sleep(POLL_INTERVAL)
            continue

        with _lock:
            _last_position = None
            _last_movement = None

        if error_message != last_error:
            print(f"[Betty] Erro ao consultar movimento do mouse: {error_message}")
            last_error = error_message

        time.sleep(POLL_INTERVAL)
