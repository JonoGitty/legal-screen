"""python3 -m unittest discover -s tests   (no Jeff, no network)"""
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from legal_screen import check as check_mod  # noqa: E402
from legal_screen.checklist import CHECKLIST  # noqa: E402
from legal_screen.chunk import chunk_text  # noqa: E402
from legal_screen.pseudo import CLOSE, OPEN, find_parties, pseudonymise  # noqa: E402

PREAMBLE = (
    'This WEB SITE HOSTING AGREEMENT ("this Agreement") is entered into this 6th day of April, 1999 '
    'by and between Centrack International, a Florida corporation ("the Customer"), and i-on interactive, '
    'a Florida corporation ("i-on"). Contact jane@centrack.example or call 561.394.9484. '
    "The Customer shall pay $450 per month. Visit www.i-on.com for the terms of service."
)


class ChunkTest(unittest.TestCase):
    def test_chunks_cover_the_text_with_true_offsets_and_overlap(self):
        text = ("Clause one is here. " * 300) + "\n\n" + ("Clause two. " * 300)
        chunks = chunk_text(text, size=1000, overlap=100)
        self.assertEqual(chunks[0].start, 0)
        self.assertEqual(chunks[-1].end, len(text))
        for c in chunks:
            self.assertEqual(text[c.start : c.end], c.text)
        for a, b in zip(chunks, chunks[1:]):
            self.assertLess(b.start, a.end, "consecutive chunks overlap")


class PseudoTest(unittest.TestCase):
    def test_both_parties_found_from_their_definitions(self):
        names = [n for n, _ in find_parties(PREAMBLE)]
        self.assertIn("Centrack International", names)
        self.assertIn("i-on interactive", names)

    def test_names_contacts_and_amounts_are_replaced_and_role_words_kept(self):
        p = pseudonymise(PREAMBLE)
        # the domain is the secret; "www." and ".com" around a placeholder identify no one
        for secret in ("Centrack", "i-on", "www.i-on.com", "jane@", "561.394", "$450"):
            self.assertNotIn(secret.lower(), p.text.lower(), secret)
        self.assertIn('("the Customer")', p.text, "a role word identifies no one and is kept")
        self.assertIn("a Florida corporation", p.text, "a description, not a name")
        self.assertNotIn("Agreement" + CLOSE, p.text, "the agreement itself is not a party")
        self.assertIn("WEB SITE HOSTING AGREEMENT", p.text)

    def test_the_same_entity_gets_the_same_placeholder_and_restores(self):
        p = pseudonymise(PREAMBLE + " Centrack International may audit i-on.")
        party = [k for k, v in p.mapping.items() if v == "Centrack International"][0]
        self.assertEqual(p.text.count(party), 2)
        restored = p.restore(p.text)
        self.assertNotIn(OPEN, restored)
        self.assertIn("Centrack International may audit", restored)

    def test_common_words_are_never_taken_as_a_party(self):
        # regression: "of" was once captured as a party and replaced everywhere. The
        # passage is from a CUAD contract (The Atticus Project, CC BY 4.0). Three
        # guards stop it (a name must start with a capital, leading connectives are
        # stripped, "business" is not a party), so it fails only if all three go.
        text = (
            "This AGREEMENT is among THE HERTZ CORPORATION, a Delaware corporation, with an address of "
            '8501 Williams Road, Estero, Florida 33928 (hereinafter "THC"). WHEREAS, THC is the owner of a '
            "unique plan or system for conducting an equipment rental business (hereinafter the "
            '"Equipment Rental Business" or "ERB" as further defined).'
        )
        p = pseudonymise(text)
        self.assertIn(" owner of a ", p.text)
        self.assertIn("address of", p.text)
        self.assertNotIn("HERTZ", p.text)
        self.assertNotIn("THC", p.text)

    def test_upper_case_company_suffixes_are_caught(self):
        # regression: "CORPORATION" / "LTD" were missed while matching was case-sensitive
        p = pseudonymise("Between WESTERN COPPER CORPORATION and GLAMIS GOLD LTD, the parties agree.")
        self.assertNotIn("WESTERN", p.text)
        self.assertNotIn("GLAMIS", p.text)

    def test_refuses_text_that_already_has_placeholder_brackets(self):
        with self.assertRaises(ValueError):
            pseudonymise(f"Already {OPEN}PARTY_A{CLOSE} here")


class CheckTest(unittest.TestCase):
    def test_verdict_bands_quote_and_honest_not_found(self):
        text = ("Recitals and background. " * 120) + (
            "12.1 This Agreement shall be governed by the laws of the State of New York. "
        ) + ("Other terms apply. " * 120)
        p_by_key = {"governing_law": 0.95, "insurance": 0.5}

        def fake_ask(chunk_text_, questions):
            hit = "governed by" in chunk_text_
            return {k: (p_by_key.get(k, 0.02) if hit or k == "insurance" else 0.02) for k in questions}

        with mock.patch.object(check_mod, "ask", side_effect=fake_ask):
            findings = {f.item.key: f for f in check_mod.check(text)}
        gl = findings["governing_law"]
        self.assertEqual(gl.verdict, "found")
        self.assertIn("governed by the laws of the State of New York", gl.quote)
        self.assertEqual(findings["insurance"].verdict, "check")
        nf = findings["audit_rights"]
        self.assertEqual(nf.verdict, "not found")
        md = check_mod.render_markdown(list(findings.values()), "x.txt")
        self.assertIn(f"not found in any of {nf.chunks_checked} passages", md)
        self.assertIn("not proof the clause is absent", md)
        self.assertEqual(len(findings), len(CHECKLIST))

    def test_quote_prefers_the_clause_over_its_heading(self):
        from legal_screen.chunk import Chunk

        item = next(i for i in CHECKLIST if i.key == "cap_on_liability")
        text = "LIMITATION OF LIABILITY\nIn no event shall either party's aggregate liability exceed the fees paid in the prior twelve months."
        q = check_mod.best_quote(item, Chunk(0, 0, len(text), text))
        self.assertTrue(q.startswith("In no event shall"), q)
        # a heading that is the only match is quoted with the sentence after it
        text = "LIMITATION OF LIABILITY\ni-on will not be liable under any circumstances for any lost profits."
        q = check_mod.best_quote(item, Chunk(0, 0, len(text), text))
        self.assertEqual(q, "LIMITATION OF LIABILITY — i-on will not be liable under any circumstances for any lost profits.")

    def test_reads_docx_without_word(self):
        xml = (
            '<?xml version="1.0"?><w:document xmlns:w="w"><w:body>'
            "<w:p><w:r><w:t>Governing law: England &amp; Wales.</w:t></w:r></w:p>"
            '<w:p><w:r><w:t xml:space="preserve">Second </w:t></w:r><w:r><w:t>para.</w:t></w:r></w:p>'
            "</w:body></w:document>"
        )
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "c.docx"
            with zipfile.ZipFile(path, "w") as z:
                z.writestr("word/document.xml", xml)
            self.assertEqual(check_mod.read_document(str(path)), "Governing law: England & Wales.\nSecond para.")


if __name__ == "__main__":
    unittest.main()


class JeffClientTest(unittest.TestCase):
    def test_a_timeout_is_retried_not_fatal(self):
        import io
        import json as _json

        from legal_screen import jeff

        calls = {"n": 0}

        def fake_urlopen(req, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise TimeoutError("timed out")
            body = _json.dumps({"answers": {"q": {"type": "noul", "noul": 0.8}}}).encode()
            resp = io.BytesIO(body)
            resp.__enter__ = lambda s=resp: s
            resp.__exit__ = lambda *a: False
            return resp

        with mock.patch.object(jeff, "_post", fake_urlopen), mock.patch.object(jeff.time, "sleep"):
            self.assertEqual(jeff.ask("text", {"q": "Is it?"}), {"q": 0.8})
        self.assertEqual(calls["n"], 2)

    def test_contract_text_only_goes_to_this_machine(self):
        from legal_screen import jeff

        sent = []
        with mock.patch.object(jeff, "_post", lambda req, timeout=None: sent.append(req)), mock.patch.dict(
            "os.environ", {}, clear=False
        ):
            os_env = __import__("os").environ
            os_env.pop("LEGAL_SCREEN_ALLOW_REMOTE_JEFF", None)
            for url in ("http://example.com:8765", "http://10.0.0.5:8765", "https://jeff.cloud.example"):
                with self.assertRaises(jeff.JeffError) as e:
                    jeff.ask("SECRET CONTRACT", {"q": "?"}, url=url)
                self.assertIn("Jeff must run on this machine", str(e.exception))
            self.assertEqual(sent, [], "nothing was sent to a remote host")
            for url in ("http://127.0.0.1:8765", "http://localhost:8765", "http://[::1]:8765"):
                jeff.require_local(url)  # no error
            os_env["LEGAL_SCREEN_ALLOW_REMOTE_JEFF"] = "1"
            jeff.require_local("http://example.com:8765")  # explicit override
            os_env.pop("LEGAL_SCREEN_ALLOW_REMOTE_JEFF")

    def test_redirects_are_never_followed(self):
        from legal_screen import jeff

        self.assertIsNone(jeff._NoRedirect().redirect_request(None, None, 302, "Found", {}, "http://evil.example"))

    def test_a_configured_proxy_is_never_used(self):
        import urllib.request

        from legal_screen import jeff

        def uses_proxy(opener):
            return any(isinstance(h, urllib.request.ProxyHandler) and h.proxies for h in opener.handlers)

        env = {"HTTP_PROXY": "http://proxy.example:3128", "http_proxy": "http://proxy.example:3128"}
        with mock.patch.dict("os.environ", env):
            self.assertTrue(uses_proxy(urllib.request.build_opener()), "the default would route via the proxy")
            self.assertFalse(uses_proxy(jeff._make_opener()), "ours never does")
