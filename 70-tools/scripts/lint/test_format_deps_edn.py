"""Unit tests for format-deps-edn (pure stdlib)."""

import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location(
    "fde", pathlib.Path(__file__).with_name("format-deps-edn.py")
)
fde = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fde)


class TokenizerTest(unittest.TestCase):
    def test_strings_keep_delims_and_semicolons_inside(self):
        toks = fde.tokenize('{:a "x; {not a comment} [b]" :b 1}')
        self.assertIn('"x; {not a comment} [b]"', toks)
        self.assertEqual(toks[0], "{")
        self.assertEqual(toks[-1], "}")

    def test_escaped_quote_inside_string(self):
        toks = fde.tokenize(r'{:a "he said \"hi\" loudly"}')
        self.assertIn(r'"he said \"hi\" loudly"', toks)

    def test_comment_outside_string(self):
        toks = fde.tokenize("[1 2 ; trailing\n 3]")
        self.assertIn("; trailing", toks)

    def test_char_literal(self):
        toks = fde.tokenize(r"[\a \newline é]")
        self.assertEqual(toks, ["[", r"\a", r"\newline", r"é", "]"])

    def test_set_and_tagged(self):
        toks = fde.tokenize('#{1 2} #inst "2026-06-12"')
        self.assertEqual(toks, ["#{", "1", "2", "}", "#inst", '"2026-06-12"'])

    def test_comma_is_whitespace(self):
        self.assertEqual(fde.tokenize("[1, 2,3]"), ["[", "1", "2", "3", "]"])


class ParserTest(unittest.TestCase):
    def test_tagged_literal_pairs_as_one_value(self):
        root = fde.parse(fde.tokenize('{:t #inst "2026-06-12" :n 1}'))
        self.assertEqual(len(root.children), 4)  # :t TAGGED :n 1
        self.assertIsInstance(root.children[1], fde.Tagged)

    def test_unbalanced_raises(self):
        with self.assertRaises(ValueError):
            fde.parse(fde.tokenize("{:a [1 2}"))


class FormatTest(unittest.TestCase):
    def test_top_level_keys_one_per_line(self):
        out = fde.format_edn('{:a 1 :b {:x 1 :y [2 3]} :c "s"}')
        self.assertEqual(out, '{:a 1\n :b {:x 1 :y [2 3]}\n :c "s"}\n')

    def test_map_vector_one_element_per_line_with_lone_closer(self):
        out = fde.format_edn('{:adrs [{:id "1"} {:id "2"}] :z 9}')
        self.assertEqual(
            out,
            '{:adrs\n [{:id "1"}\n  {:id "2"}\n ]\n :z 9}\n',
        )

    def test_single_element_vector_stays_inline(self):
        out = fde.format_edn('{:adrs [{:id "1"}]}')
        self.assertEqual(out, '{:adrs [{:id "1"}]}\n')

    def test_mixed_vector_stays_inline(self):
        out = fde.format_edn('{:v [1 {:a 2} 3]}')
        self.assertEqual(out, "{:v [1 {:a 2} 3]}\n")

    def test_idempotent(self):
        src = '{:adrs [{:id "1"} {:id "2"}] :a 1}'
        once = fde.format_edn(src)
        self.assertEqual(fde.format_edn(once), once)

    def test_token_stream_preserved_on_nasty_input(self):
        src = '{:a "}]) ; \\" tricky" :tags #{:x :y} :t #inst "2026-01-01" :v [{:m 1} {:m 2}]}'
        out = fde.format_edn(src)
        self.assertEqual(fde.tokenize(out), fde.tokenize(src))

    def test_append_is_single_line_diff(self):
        base = fde.format_edn('{:adrs [{:id "1"} {:id "2"}]}')
        grown = fde.format_edn('{:adrs [{:id "1"} {:id "2"} {:id "3"}]}')
        b, g = base.splitlines(), grown.splitlines()
        added = [l for l in g if l not in b]
        self.assertEqual(added, ['  {:id "3"}'])


class AppendAdrsTest(unittest.TestCase):
    def test_appends_structurally_and_canonically(self):
        src = '{:a 1 :adrs [{:id "1"} {:id "2"}]}'
        out = fde.append_adrs(src, '{:id "3" :title "x (y; z]"}')
        self.assertIn(' {:id "3" :title "x (y; z]"}', out)
        self.assertEqual(fde.format_once(out), out)

    def test_multiple_entries(self):
        src = '{:adrs [{:id "1"} {:id "9"}]}'
        out = fde.append_adrs(src, '{:id "2"} {:id "3"}')
        self.assertIn('{:id "2"}', out)
        self.assertIn('{:id "3"}', out)

    def test_rejects_invalid_source(self):
        with self.assertRaises(ValueError):
            fde.append_adrs('{:adrs [{:id "broken ]}', '{:id "2"}')

    def test_rejects_non_map_entry(self):
        with self.assertRaises(ValueError):
            fde.append_adrs('{:adrs [{:id "1"} {:id "2"}]}', '[1 2]')


if __name__ == "__main__":
    unittest.main()
