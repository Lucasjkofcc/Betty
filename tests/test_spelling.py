import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from betty.skills import spelling


class SpellingHelpersTests(unittest.TestCase):
    def test_sentence_at_caret_returns_sentence_and_offset(self):
        text = "Primeira frase. erro de ortografia! Última."

        sentence, offset = spelling._sentence_at_caret(text, 24)

        self.assertEqual(sentence, "erro de ortografia")
        self.assertEqual(text[offset:offset + len(sentence)], sentence)

    def test_sentence_at_caret_checks_completed_sentence(self):
        for text in ("erro de ortografia.", "erro de ortografia. "):
            with self.subTest(text=text):
                sentence, offset = spelling._sentence_at_caret(text, len(text))

                self.assertEqual(sentence, "erro de ortografia")
                self.assertEqual(text[offset:offset + len(sentence)], sentence)

    def test_language_tool_utf16_offsets_handle_emoji(self):
        field = spelling.TextField(":1.2", "/field", "😀 errur", 8)
        response = {
            "matches": [
                {
                    "offset": 3,
                    "length": 5,
                    "replacements": [{"value": "error"}],
                    "rule": {"issueType": "misspelling"},
                }
            ]
        }

        suggestion = spelling._suggestion_from_response(
            response,
            field,
            field.text,
            0,
        )

        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.incorrect, "errur")
        self.assertEqual(suggestion.start, 2)
        self.assertEqual(suggestion.end, 7)
        self.assertIn("erro", suggestion.comment)

    def test_suggestion_nearest_to_caret_is_selected(self):
        text = "eu nao sei portugues"
        field = spelling.TextField(":1.2", "/field", text, len(text))
        response = {
            "matches": [
                {
                    "offset": 0,
                    "length": 2,
                    "replacements": [{"value": "Eu"}],
                    "rule": {"issueType": "typographical"},
                },
                {
                    "offset": 3,
                    "length": 3,
                    "replacements": [{"value": "não"}],
                    "rule": {"issueType": "misspelling"},
                },
                {
                    "offset": 11,
                    "length": 9,
                    "replacements": [{"value": "português"}],
                    "rule": {"issueType": "misspelling"},
                },
            ]
        }

        suggestion = spelling._suggestion_from_response(
            response,
            field,
            text,
            0,
        )

        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion.incorrect, "portugues")
        self.assertEqual(suggestion.replacement, "português")

    def test_local_language_tool_rejects_remote_urls(self):
        with patch.object(
            spelling,
            "LANGUAGETOOL_URL",
            "https://api.languagetool.org/v2/check",
        ):
            with self.assertRaisesRegex(ValueError, "não será enviado"):
                spelling._check_local_language_tool("texto privado")

    def test_local_language_tool_accepts_loopback_server(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"matches":[]}'
        opener = MagicMock()
        opener.open.return_value = response

        with (
            patch.object(
                spelling,
                "LANGUAGETOOL_URL",
                "http://127.0.0.1:8081/v2/check",
            ),
            patch.object(spelling, "build_opener", return_value=opener),
        ):
            result = spelling._check_local_language_tool("texto de teste")

        self.assertEqual(result, {"matches": []})
        request = opener.open.call_args.args[0]
        self.assertEqual(request.get_method(), "POST")
        self.assertIn(b"language=pt-BR", request.data)
        self.assertIn(b"texto+de+teste", request.data)


class SpellingReplacementTests(unittest.IsolatedAsyncioTestCase):
    async def test_changed_field_is_not_replaced(self):
        field = spelling.TextField(":1.2", "/field", "texto errado", 12)
        suggestion = spelling.SpellingSuggestion(
            field=field,
            start=6,
            end=12,
            incorrect="errado",
            replacement="certo",
            comment="Comentário da Betty.",
        )

        with patch.object(
            spelling,
            "_dbus_call",
            new_callable=AsyncMock,
            return_value=["texto atualizado"],
        ) as dbus_call:
            await spelling._replace_suggestion(MagicMock(), suggestion)

        self.assertEqual(dbus_call.await_count, 1)
        self.assertEqual(dbus_call.await_args.args[4], "GetText")

    async def test_notification_coordinates_use_dbus_variants(self):
        field = spelling.TextField(":1.2", "/field", "portugues", 9)
        suggestion = spelling.SpellingSuggestion(
            field=field,
            start=0,
            end=9,
            incorrect="portugues",
            replacement="português",
            comment="Sugestão de ortografia.",
        )

        with (
            patch.object(
                spelling,
                "_character_extents",
                new_callable=AsyncMock,
                return_value=(123, 456, 10, 20),
            ),
            patch.object(
                spelling,
                "_dbus_call",
                new_callable=AsyncMock,
                return_value=[1],
            ) as dbus_call,
        ):
            await spelling._show_suggestion(
                MagicMock(),
                MagicMock(),
                suggestion,
            )

        hints = dbus_call.await_args.kwargs["body"][6]
        self.assertEqual(hints["x"], spelling.Variant("i", 123))
        self.assertEqual(hints["y"], spelling.Variant("i", 432))


if __name__ == "__main__":
    unittest.main()
