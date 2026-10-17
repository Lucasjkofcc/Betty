import asyncio
import ipaddress
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, build_opener

from dbus_next import BusType, Message, MessageType, Variant
from dbus_next.aio import MessageBus
from dbus_next.errors import DBusError


LANGUAGETOOL_URL = os.environ.get(
    "BETTY_LANGUAGETOOL_URL",
    "http://127.0.0.1:8081/v2/check",
)
LANGUAGE = "pt-BR"
POLL_INTERVAL = 1.5
DEBOUNCE_SECONDS = 1.5
REQUEST_TIMEOUT = 5
DBUS_TIMEOUT = 1
MAX_TREE_NODES = 2000
MAX_TREE_DEPTH = 16
MAX_FIELD_LENGTH = 10000

ACCESSIBLE_BUS = "org.a11y.atspi.Registry"
ACCESSIBLE_ROOT = "/org/a11y/atspi/accessible/root"
ACCESSIBLE_INTERFACE = "org.a11y.atspi.Accessible"
TEXT_INTERFACE = "org.a11y.atspi.Text"
EDITABLE_TEXT_INTERFACE = "org.a11y.atspi.EditableText"
NOTIFICATIONS_BUS = "org.freedesktop.Notifications"
NOTIFICATIONS_PATH = "/org/freedesktop/Notifications"
NOTIFICATIONS_INTERFACE = "org.freedesktop.Notifications"

STATE_EDITABLE = 7
STATE_FOCUSED = 12


@dataclass(frozen=True)
class TextField:
    bus_name: str
    object_path: str
    text: str
    caret: int


@dataclass(frozen=True)
class SpellingSuggestion:
    field: TextField
    start: int
    end: int
    incorrect: str
    replacement: str
    comment: str


def _python_index_for_utf16(text: str, offset: int) -> int:
    """Convert LanguageTool's UTF-16 offsets to Python character offsets."""
    consumed = 0
    for index, character in enumerate(text):
        if consumed >= offset:
            return index
        consumed += 2 if ord(character) > 0xFFFF else 1
    return len(text)


def _sentence_at_caret(text: str, caret: int) -> tuple[str, int]:
    caret = min(max(caret, 0), len(text))
    delimiters = (".", "!", "?", "\n")
    left_boundary = max(
        (text.rfind(mark, 0, caret) for mark in delimiters),
        default=-1,
    )
    left = left_boundary + 1
    right_candidates = [
        position
        for mark in delimiters
        if (position := text.find(mark, caret)) >= 0
    ]
    right = min(right_candidates, default=len(text))

    if not text[left:caret].strip() and left_boundary >= 0:
        left = max(
            (text.rfind(mark, 0, left_boundary) for mark in delimiters),
            default=-1,
        ) + 1
        right = left_boundary

    while left < right and text[left].isspace():
        left += 1
    while right > left and text[right - 1].isspace():
        right -= 1
    return text[left:right], left


def _comment_for_match(
    match: Mapping[str, Any],
    incorrect: str,
    replacement: str,
) -> str:
    rule = match.get("rule", {})
    if not isinstance(rule, Mapping):
        rule = {}
    issue_type = str(rule.get("issueType", "")).lower()
    category_data = rule.get("category", {})
    if not isinstance(category_data, Mapping):
        category_data = {}
    category = str(category_data.get("id", "")).lower()
    if issue_type in {"misspelling", "typographical"} or category in {
        "typos",
        "misspelling",
    }:
        return (
            f"Mestre, “{incorrect}” está escrito incorretamente. "
            f"Betty sugere “{replacement}”."
        )
    return (
        "Mestre, esta construção parece ter um problema gramatical. "
        f"Betty sugere “{replacement}”."
    )


def _suggestion_from_response(
    response: Mapping[str, Any],
    field: TextField,
    sentence: str,
    sentence_offset: int,
) -> SpellingSuggestion | None:
    suggestions = []
    for match in response.get("matches", []):
        if not isinstance(match, Mapping):
            continue
        replacements = match.get("replacements", [])
        if not isinstance(replacements, list) or not replacements:
            continue
        replacement_data = replacements[0]
        if not isinstance(replacement_data, Mapping):
            continue

        start = _python_index_for_utf16(sentence, int(match.get("offset", 0)))
        end = _python_index_for_utf16(
            sentence,
            int(match.get("offset", 0)) + int(match.get("length", 0)),
        )
        if start >= end or end > len(sentence):
            continue

        incorrect = sentence[start:end]
        replacement = str(replacement_data.get("value", ""))
        if not incorrect or not replacement or incorrect == replacement:
            continue

        suggestions.append(
            SpellingSuggestion(
                field=field,
                start=sentence_offset + start,
                end=sentence_offset + end,
                incorrect=incorrect,
                replacement=replacement,
                comment=_comment_for_match(match, incorrect, replacement),
            )
        )
    if not suggestions:
        return None

    return min(
        suggestions,
        key=lambda suggestion: (
            0
            if suggestion.start <= field.caret <= suggestion.end
            else min(
                abs(field.caret - suggestion.start),
                abs(field.caret - suggestion.end),
            )
        ),
    )


def _check_local_language_tool(text: str) -> dict:
    url = LANGUAGETOOL_URL
    parsed_url = urlparse(url)
    try:
        is_loopback = (
            parsed_url.hostname is not None
            and ipaddress.ip_address(parsed_url.hostname).is_loopback
        )
    except ValueError:
        is_loopback = False
    if parsed_url.scheme != "http" or not is_loopback:
        raise ValueError(
            "O LanguageTool deve usar um endereço HTTP local; "
            "o texto digitado não será enviado a um serviço remoto."
        )

    payload = urllib.parse.urlencode(
        {"language": LANGUAGE, "text": text},
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    class RejectRedirects(HTTPRedirectHandler):
        def redirect_request(self, request, file, code, message, headers, url):
            return None

    try:
        opener = build_opener(RejectRedirects)
        with opener.open(request, timeout=REQUEST_TIMEOUT) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as error:
        raise ConnectionError(
            f"Não foi possível acessar o LanguageTool local em {url}: {error}"
        ) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(
            f"O LanguageTool local retornou uma resposta inválida: {error}"
        ) from error
    if not isinstance(result, dict) or not isinstance(result.get("matches"), list):
        raise ValueError(
            "O LanguageTool local retornou uma resposta sem a lista de correções."
        )
    return result


async def _dbus_call(
    bus: MessageBus,
    destination: str,
    path: str,
    interface: str,
    member: str,
    *,
    signature: str = "",
    body: list | None = None,
) -> list:
    reply = await asyncio.wait_for(
        bus.call(
            Message(
                destination=destination,
                path=path,
                interface=interface,
                member=member,
                signature=signature,
                body=body or [],
            )
        ),
        timeout=DBUS_TIMEOUT,
    )
    if reply.message_type == MessageType.ERROR:
        raise DBusError(
            reply.error_name or "org.freedesktop.DBus.Error.Failed",
            reply.body[0] if reply.body else "D-Bus method call failed",
        )
    return reply.body


async def _get_active_text_field(accessibility_bus: MessageBus) -> TextField | None:
    frontier = [(ACCESSIBLE_BUS, ACCESSIBLE_ROOT, 0)]
    visited = 0

    while frontier and visited < MAX_TREE_NODES:
        batch = frontier[:MAX_TREE_NODES - visited]
        frontier = []
        states = await asyncio.gather(
            *(
                _dbus_call(
                    accessibility_bus,
                    bus_name,
                    path,
                    ACCESSIBLE_INTERFACE,
                    "GetState",
                )
                for bus_name, path, _ in batch
            ),
            return_exceptions=True,
        )
        visited += len(batch)
        focused_fields = []

        for (bus_name, path, depth), result in zip(batch, states):
            if isinstance(result, Exception):
                continue
            state = set(result[0])
            if STATE_FOCUSED in state:
                try:
                    interfaces = await _dbus_call(
                        accessibility_bus,
                        bus_name,
                        path,
                        ACCESSIBLE_INTERFACE,
                        "GetInterfaces",
                    )
                except (DBusError, asyncio.TimeoutError):
                    continue
                if (
                    STATE_EDITABLE in state
                    and TEXT_INTERFACE in interfaces[0]
                    and EDITABLE_TEXT_INTERFACE in interfaces[0]
                ):
                    focused_fields.append((bus_name, path))

        if focused_fields:
            for bus_name, path in focused_fields:
                try:
                    role = await _dbus_call(
                        accessibility_bus,
                        bus_name,
                        path,
                        ACCESSIBLE_INTERFACE,
                        "GetRoleName",
                    )
                except (DBusError, asyncio.TimeoutError):
                    continue
                if "password" in str(role[0]).lower():
                    continue
                try:
                    text, caret = await asyncio.gather(
                        _dbus_call(
                            accessibility_bus,
                            bus_name,
                            path,
                            TEXT_INTERFACE,
                            "GetText",
                            signature="ii",
                            body=[0, -1],
                        ),
                        _dbus_call(
                            accessibility_bus,
                            bus_name,
                            path,
                            TEXT_INTERFACE,
                            "GetCaretOffset",
                        ),
                    )
                except (DBusError, asyncio.TimeoutError):
                    continue
                field_text = str(text[0])
                if len(field_text) > MAX_FIELD_LENGTH:
                    continue
                return TextField(
                    bus_name=bus_name,
                    object_path=path,
                    text=field_text,
                    caret=int(caret[0]),
                )

        child_lists = await asyncio.gather(
            *(
                _dbus_call(
                    accessibility_bus,
                    bus_name,
                    path,
                    ACCESSIBLE_INTERFACE,
                    "GetChildren",
                )
                for bus_name, path, depth in batch
                if depth < MAX_TREE_DEPTH
            ),
            return_exceptions=True,
        )
        child_index = 0
        for bus_name, _, depth in batch:
            if depth >= MAX_TREE_DEPTH:
                continue
            children = child_lists[child_index]
            child_index += 1
            if isinstance(children, Exception):
                continue
            frontier.extend(
                (str(child_bus), str(child_path), depth + 1)
                for child_bus, child_path in children[0]
            )

    return None


async def _character_extents(
    accessibility_bus: MessageBus,
    field: TextField,
    offset: int,
) -> tuple[int, int, int, int] | None:
    try:
        result = await _dbus_call(
            accessibility_bus,
            field.bus_name,
            field.object_path,
            TEXT_INTERFACE,
            "GetCharacterExtents",
            signature="ii",
            body=[offset, 0],
        )
    except (DBusError, asyncio.TimeoutError):
        return None

    if len(result) < 4:
        return None
    try:
        return (
            int(result[0]),
            int(result[1]),
            int(result[2]),
            int(result[3]),
        )
    except (TypeError, ValueError):
        return None


async def _show_suggestion(
    session_bus: MessageBus,
    accessibility_bus: MessageBus,
    suggestion: SpellingSuggestion,
) -> int:
    body = (
        f'{suggestion.incorrect} → {suggestion.replacement}\n'
        f"{suggestion.comment}"
    )
    hints: dict[str, Variant] = {}
    extents = await _character_extents(accessibility_bus, suggestion.field, suggestion.start)
    if extents is not None:
        x, y, _, _ = extents
        hints.update(
            {
                "x": Variant("i", x),
                "y": Variant("i", max(0, y - 24)),
            }
        )

    result = await _dbus_call(
        session_bus,
        NOTIFICATIONS_BUS,
        NOTIFICATIONS_PATH,
        NOTIFICATIONS_INTERFACE,
        "Notify",
        signature="susssasa{sv}i",
        body=[
            "Betty",
            0,
            "accessories-dictionary",
            "Sugestão de ortografia",
            body,
            ["replace", "Aceitar correção", "ignore", "Ignorar"],
            hints,
            15000,
        ],
    )
    return int(result[0])


async def _replace_suggestion(
    accessibility_bus: MessageBus,
    suggestion: SpellingSuggestion,
) -> None:
    field = suggestion.field
    try:
        current_text = await _dbus_call(
            accessibility_bus,
            field.bus_name,
            field.object_path,
            TEXT_INTERFACE,
            "GetText",
            signature="ii",
            body=[0, -1],
        )
    except (DBusError, asyncio.TimeoutError) as error:
        print(f"[Betty] Não foi possível acessar o campo para corrigir: {error}")
        return

    text = str(current_text[0])
    if (
        text != field.text
        or text[suggestion.start:suggestion.end] != suggestion.incorrect
    ):
        print("[Betty] O texto mudou; a sugestão antiga foi descartada.")
        return

    new_text = (
        text[:suggestion.start]
        + suggestion.replacement
        + text[suggestion.end:]
    )
    try:
        result = await _dbus_call(
            accessibility_bus,
            field.bus_name,
            field.object_path,
            EDITABLE_TEXT_INTERFACE,
            "SetTextContents",
            signature="s",
            body=[new_text],
        )
        if not result[0]:
            print("[Betty] O aplicativo recusou a substituição do texto.")
            return
    except (DBusError, asyncio.TimeoutError) as error:
        print(f"[Betty] Não foi possível substituir o trecho incorreto: {error}")
        return

    new_caret = field.caret
    if field.caret > suggestion.end:
        new_caret += len(suggestion.replacement) - (
            suggestion.end - suggestion.start
        )
    elif field.caret >= suggestion.start:
        new_caret = suggestion.start + len(suggestion.replacement)
    try:
        await _dbus_call(
            accessibility_bus,
            field.bus_name,
            field.object_path,
            TEXT_INTERFACE,
            "SetCaretOffset",
            signature="i",
            body=[new_caret],
        )
    except (DBusError, asyncio.TimeoutError) as error:
        print(
            "[Betty] Correção aplicada, mas não foi possível restaurar "
            f"a posição do cursor: {error}"
        )
        return
    print(f"[Betty] Correção aplicada: {suggestion.replacement}")


def _handle_notification_signal(
    message: Message,
    suggestions: dict[int, SpellingSuggestion],
    accessibility_bus: MessageBus,
) -> bool:
    if (
        message.message_type != MessageType.SIGNAL
        or message.interface != NOTIFICATIONS_INTERFACE
    ):
        return False

    if message.member == "ActionInvoked" and len(message.body) == 2:
        notification_id, action = int(message.body[0]), str(message.body[1])
        suggestion = suggestions.pop(notification_id, None)
        if suggestion is not None and action == "replace":
            asyncio.create_task(_replace_suggestion(accessibility_bus, suggestion))
        return False

    if message.member == "NotificationClosed" and message.body:
        suggestions.pop(int(message.body[0]), None)
    return False


async def _monitor_spelling() -> None:
    session_bus = await MessageBus(bus_type=BusType.SESSION).connect()
    try:
        accessibility_status = await _dbus_call(
            session_bus,
            "org.a11y.Bus",
            "/org/a11y/bus",
            "org.freedesktop.DBus.Properties",
            "Get",
            signature="ss",
            body=["org.a11y.Status", "IsEnabled"],
        )
        if not accessibility_status[0].value:
            raise ConnectionError(
                "A acessibilidade AT-SPI está desativada. "
                "Ative-a nas configurações do ambiente gráfico para usar a skill."
            )
        address = await _dbus_call(
            session_bus,
            "org.a11y.Bus",
            "/org/a11y/bus",
            "org.a11y.Bus",
            "GetAddress",
        )
        accessibility_bus = await MessageBus(bus_address=address[0]).connect()
    except BaseException:
        session_bus.disconnect()
        raise

    suggestions: dict[int, SpellingSuggestion] = {}
    await _dbus_call(
        session_bus,
        "org.freedesktop.DBus",
        "/org/freedesktop/DBus",
        "org.freedesktop.DBus",
        "AddMatch",
        signature="s",
        body=[
            "type='signal',sender='org.freedesktop.Notifications',"
            "interface='org.freedesktop.Notifications'"
        ],
    )
    session_bus.add_message_handler(
        lambda message: _handle_notification_signal(
            message,
            suggestions,
            accessibility_bus,
        )
    )

    last_signature = None
    stable_since = 0.0
    last_checked_signature = None
    last_error = None

    print(
        "[Betty] Corretor ortográfico iniciado. "
        f"LanguageTool local: {LANGUAGETOOL_URL}"
    )
    while True:
        try:
            field = await _get_active_text_field(accessibility_bus)
            if field is None:
                last_signature = None
                await asyncio.sleep(POLL_INTERVAL)
                continue

            sentence, sentence_offset = _sentence_at_caret(
                field.text,
                field.caret,
            )
            if not sentence:
                await asyncio.sleep(POLL_INTERVAL)
                continue

            signature = (field.bus_name, field.object_path, sentence)
            if signature != last_signature:
                last_signature = signature
                stable_since = time.monotonic()
                await asyncio.sleep(POLL_INTERVAL)
                continue
            if (
                signature == last_checked_signature
                or time.monotonic() - stable_since < DEBOUNCE_SECONDS
            ):
                await asyncio.sleep(POLL_INTERVAL)
                continue

            response = await asyncio.to_thread(
                _check_local_language_tool,
                sentence,
            )
            current_field = await _get_active_text_field(accessibility_bus)
            if (
                current_field is None
                or current_field.bus_name != field.bus_name
                or current_field.object_path != field.object_path
                or current_field.text != field.text
            ):
                last_signature = None
                await asyncio.sleep(POLL_INTERVAL)
                continue
            current_sentence, _ = _sentence_at_caret(
                current_field.text,
                current_field.caret,
            )
            if current_sentence != sentence:
                last_signature = None
                await asyncio.sleep(POLL_INTERVAL)
                continue

            suggestion = _suggestion_from_response(
                response,
                field,
                sentence,
                sentence_offset,
            )
            last_checked_signature = signature
            if suggestion is not None:
                notification_id = await _show_suggestion(
                    session_bus,
                    accessibility_bus,
                    suggestion,
                )
                suggestions[notification_id] = suggestion
                if len(suggestions) > 32:
                    suggestions.pop(next(iter(suggestions)))
            last_error = None
        except (ConnectionError, DBusError, OSError, ValueError, asyncio.TimeoutError) as error:
            error_message = str(error)
            if error_message != last_error:
                print(f"[Betty] Erro no corretor ortográfico: {error_message}")
                last_error = error_message
            await asyncio.sleep(10)
            last_signature = None
            continue

        await asyncio.sleep(POLL_INTERVAL)


def monitor_spelling() -> None:
    last_error = None
    while True:
        try:
            asyncio.run(_monitor_spelling())
        except (ConnectionError, DBusError, OSError, asyncio.TimeoutError) as error:
            error_message = str(error)
            if error_message != last_error:
                print(f"[Betty] Monitor de ortografia indisponível: {error_message}")
                last_error = error_message
            time.sleep(10)
