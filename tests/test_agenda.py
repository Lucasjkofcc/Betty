import importlib.util
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "betty"
    / "skills"
    / "agenda.py"
)
spec = importlib.util.spec_from_file_location("betty_agenda", MODULE_PATH)
agenda = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agenda)


class AgendaTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = agenda.AGENDA_FILE
        agenda.AGENDA_FILE = Path(self.temp_dir.name) / "agenda.json"

    def tearDown(self):
        agenda.AGENDA_FILE = self.original_path
        self.temp_dir.cleanup()

    def test_due_one_off_reminder_is_notified_once_until_completed(self):
        now = datetime(2026, 11, 20, 12, 0)
        reminder = agenda.create_reminder(
            (now + timedelta(minutes=5)).isoformat(),
            "once",
            "buscar encomenda",
            now=now,
        )
        due_at = reminder["due_at"]
        due_time = datetime.fromisoformat(due_at)

        self.assertEqual(agenda.due_reminders(now=due_time), [reminder])
        agenda.mark_reminder_notified(reminder["id"], due_at, now=due_time)
        self.assertEqual(agenda.due_reminders(now=due_time), [])
        self.assertEqual(agenda.list_today_reminders(now=due_time)[0]["id"], reminder["id"])
        self.assertTrue(agenda.complete_reminder(reminder["id"]))
        self.assertEqual(agenda.list_pending_reminders(), [])

    def test_recurring_reminder_advances_and_remains_on_today_agenda(self):
        now = datetime(2026, 11, 20, 8, 0)
        reminder = agenda.create_reminder(
            (now + timedelta(minutes=1)).isoformat(),
            "daily",
            "tomar remédio",
            now=now,
        )
        due_at = reminder["due_at"]
        due_time = datetime.fromisoformat(due_at)

        agenda.mark_reminder_notified(reminder["id"], due_at, now=due_time)

        pending = agenda.list_pending_reminders()[0]
        self.assertEqual(
            datetime.fromisoformat(pending["due_at"]),
            due_time + timedelta(days=1),
        )
        self.assertEqual(agenda.due_reminders(now=due_time), [])
        self.assertEqual(agenda.list_today_reminders(now=due_time)[0]["id"], reminder["id"])

    def test_weekly_reminder_advances_by_one_week(self):
        now = datetime(2026, 11, 20, 8, 0)
        reminder = agenda.create_reminder(
            (now + timedelta(minutes=1)).isoformat(),
            "weekly",
            "reunião",
            now=now,
        )
        due_at = reminder["due_at"]
        due_time = datetime.fromisoformat(due_at)

        agenda.mark_reminder_notified(reminder["id"], due_at, now=due_time)

        pending = agenda.list_pending_reminders()[0]
        self.assertEqual(
            datetime.fromisoformat(pending["due_at"]),
            due_time + timedelta(weeks=1),
        )

    def test_rejects_past_reminder(self):
        now = datetime(2026, 11, 20, 12, 0)

        with self.assertRaises(ValueError):
            agenda.create_reminder(
                (now - timedelta(minutes=1)).isoformat(),
                "once",
                "buscar encomenda",
                now=now,
            )


if __name__ == "__main__":
    unittest.main()
