import json
import os
import tempfile
import threading
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path


AGENDA_FILE = Path("agenda.json")
RECURRENCES = {"once", "daily", "weekly"}
_lock = threading.RLock()


def _local_time(value: datetime) -> datetime:
    if value.tzinfo is not None:
        return value.astimezone().replace(tzinfo=None)
    return value


def _read_reminders() -> list[dict]:
    try:
        with AGENDA_FILE.open(encoding="utf-8") as file:
            reminders = json.load(file)
    except FileNotFoundError:
        return []
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Não foi possível ler a agenda: {error}") from error

    if not isinstance(reminders, list):
        raise ValueError("O arquivo da agenda precisa conter uma lista.")

    for reminder in reminders:
        if not isinstance(reminder, dict):
            raise ValueError("A agenda contém um lembrete inválido.")
        if (
            not isinstance(reminder.get("id"), int)
            or not isinstance(reminder.get("title"), str)
            or not isinstance(reminder.get("due_at"), str)
            or not isinstance(reminder.get("recurrence"), str)
            or reminder.get("recurrence") not in RECURRENCES
            or not isinstance(reminder.get("status"), str)
            or reminder.get("status") not in {"pending", "done"}
            or "notified_at" not in reminder
        ):
            raise ValueError("A agenda contém um lembrete inválido.")
        datetime.fromisoformat(reminder["due_at"])
        if reminder.get("notified_at") is not None:
            if not isinstance(reminder["notified_at"], str):
                raise ValueError("A agenda contém um lembrete inválido.")
            datetime.fromisoformat(reminder["notified_at"])

    return reminders


def _write_reminders(reminders: list[dict]) -> None:
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=AGENDA_FILE.parent,
            prefix=f".{AGENDA_FILE.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary_path = Path(file.name)
            json.dump(reminders, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary_path, AGENDA_FILE)
    except OSError as error:
        raise RuntimeError(f"Não foi possível salvar a agenda: {error}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def create_reminder(
    due_at: str,
    recurrence: str,
    title: str,
    *,
    now: datetime | None = None,
) -> dict:
    try:
        due = datetime.fromisoformat(due_at)
    except ValueError as error:
        raise ValueError("A data e o horário do lembrete são inválidos.") from error

    due = _local_time(due)
    if not isinstance(recurrence, str) or recurrence not in RECURRENCES:
        raise ValueError("A recorrência deve ser única, diária ou semanal.")
    if not title.strip():
        raise ValueError("O lembrete precisa ter uma descrição.")
    current_time = datetime.now() if now is None else _local_time(now)
    if due <= current_time:
        raise ValueError("A data e o horário precisam estar no futuro.")

    with _lock:
        reminders = _read_reminders()
        reminder = {
            "id": max((item["id"] for item in reminders), default=0) + 1,
            "title": title.strip(),
            "due_at": due.isoformat(timespec="minutes"),
            "recurrence": recurrence,
            "status": "pending",
            "notified_at": None,
        }
        reminders.append(reminder)
        _write_reminders(reminders)
    return reminder.copy()


def list_pending_reminders() -> list[dict]:
    with _lock:
        reminders = [
            reminder.copy()
            for reminder in _read_reminders()
            if reminder["status"] == "pending"
        ]
    return sorted(reminders, key=lambda reminder: reminder["due_at"])


def list_today_reminders(*, now: datetime | None = None) -> list[dict]:
    current_time = datetime.now() if now is None else _local_time(now)
    today = current_time.date()
    with _lock:
        reminders = []
        for reminder in _read_reminders():
            if reminder["status"] != "pending":
                continue
            due_today = datetime.fromisoformat(reminder["due_at"]).date() == today
            notified_today = (
                reminder["notified_at"] is not None
                and datetime.fromisoformat(reminder["notified_at"]).date() == today
            )
            if due_today or notified_today:
                reminders.append(reminder.copy())
    return sorted(
        reminders,
        key=lambda reminder: (
            reminder["due_at"]
            if datetime.fromisoformat(reminder["due_at"]).date() == today
            else reminder["notified_at"]
        ),
    )


def complete_reminder(reminder_id: int) -> bool:
    with _lock:
        reminders = _read_reminders()
        for reminder in reminders:
            if reminder["id"] == reminder_id and reminder["status"] == "pending":
                reminder["status"] = "done"
                _write_reminders(reminders)
                return True
    return False


def due_reminders(*, now: datetime | None = None) -> list[dict]:
    current_time = datetime.now() if now is None else _local_time(now)
    with _lock:
        return [
            reminder.copy()
            for reminder in _read_reminders()
            if reminder["status"] == "pending"
            and datetime.fromisoformat(reminder["due_at"]) <= current_time
            and reminder["notified_at"] != reminder["due_at"]
        ]


def mark_reminder_notified(
    reminder_id: int,
    due_at: str,
    *,
    now: datetime | None = None,
) -> None:
    with _lock:
        reminders = _read_reminders()
        for reminder in reminders:
            if (
                reminder["id"] != reminder_id
                or reminder["status"] != "pending"
                or reminder["due_at"] != due_at
            ):
                continue

            reminder["notified_at"] = due_at
            if reminder["recurrence"] != "once":
                interval = (
                    timedelta(days=1)
                    if reminder["recurrence"] == "daily"
                    else timedelta(weeks=1)
                )
                previous_due = datetime.fromisoformat(due_at)
                current_time = datetime.now() if now is None else _local_time(now)
                missed_occurrences = (current_time - previous_due) // interval + 1
                next_due = previous_due + interval * missed_occurrences
                reminder["due_at"] = next_due.isoformat(timespec="minutes")
            _write_reminders(reminders)
            return


def monitor_reminders(
    is_busy: Callable[[], bool],
    notify: Callable[[list[dict]], None],
    *,
    interval: int = 15,
) -> None:
    import time

    while True:
        if not is_busy():
            try:
                reminders = due_reminders()
                if reminders:
                    notify(reminders)
                    for reminder in reminders:
                        mark_reminder_notified(
                            reminder["id"],
                            reminder["due_at"],
                        )
            except (OSError, RuntimeError, ValueError) as error:
                print(f"[Betty] Não foi possível processar a agenda: {error}")
        time.sleep(interval)
