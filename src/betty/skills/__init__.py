from .battery import battery_check, get_battery, has_battery
from .tts import speak, audio_queue
from .stt import (
    listen,
    listen_for_command,
    MicrophoneError,
    WakeWordConfigurationError,
)
from .program import open_program, open_steam_game
from .system import (
    cpu_info,
    cpu_check,
    cpu_percent,
    get_uptime_seconds,
    ram_info,
    disk_info,
    temperatures,
    uptime_info,
)
from .time import get_time
from .agenda import (
    complete_reminder,
    create_reminder,
    due_reminders,
    list_pending_reminders,
    list_today_reminders,
    mark_reminder_notified,
    monitor_reminders,
)
from .volume import volume_now, volume_up, volume_down, mute
from .web import search_web
from .poweroff import poweroff, reboot
from .calculator import calcular
from .tela import ocr, analyze_screen
from .facial_check import facial_check, has_camera
from .temperature import get_temperature
from .media import (
    pausar_temporario,
    retomar_temporario,
    proxima_media,
    anterior_media,
)
from .attention import (
    check_attention,
    check_night_attention,
    check_uptime_attention,
    get_attention_state,
    monitor_attention,
    register_interaction,
)
from .mouse_activity import monitor_mouse_activity, mouse_active_within
from .spelling import monitor_spelling
