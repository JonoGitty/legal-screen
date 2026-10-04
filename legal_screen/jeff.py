"""A minimal client for a local Jeff server (firelex/jeff, POST /v1/systemone).

Jeff answers each question about a passage with P(yes). It is single-flight:
an overlapping request gets 529 with Retry-After, so calls are retried.

Contract text goes ONLY to a Jeff server on this machine: a URL whose host
isn't localhost, 127.0.0.1 or ::1 is refused before anything is sent, unless
LEGAL_SCREEN_ALLOW_REMOTE_JEFF=1 says otherwise. Redirects are never
followed, so a local server cannot bounce the text elsewhere, and proxies
(HTTP_PROXY and friends) are ignored, so a configured proxy never sees it.
"""
import json
import os
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse

DEFAULT_URL = os.environ.get("JEFF_URL", "http://127.0.0.1:8765")
DEFAULT_MODEL = os.environ.get("JEFF_MODEL", "jeff-qwen3.5-0.8b")


LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


class JeffError(RuntimeError):
    pass


def require_local(url: str) -> None:
    host = urlparse(url).hostname
    if host in LOCAL_HOSTS or os.environ.get("LEGAL_SCREEN_ALLOW_REMOTE_JEFF") == "1":
        return
    raise JeffError(
        f"refusing to send contract text to {host!r}: Jeff must run on this machine "
        "(set LEGAL_SCREEN_ALLOW_REMOTE_JEFF=1 to override)"
    )


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # a 3xx becomes an HTTPError instead of a second request


def _make_opener() -> urllib.request.OpenerDirector:
    # ProxyHandler({}) replaces the default one that reads HTTP_PROXY etc.: no proxy at all
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)


_OPENER = _make_opener()


def _post(req: urllib.request.Request, timeout: float):
    return _OPENER.open(req, timeout=timeout)


def ask(text: str, questions: dict[str, str], url: str = DEFAULT_URL, model: str = DEFAULT_MODEL, retries: int = 5) -> dict[str, float]:
    """P(yes) for each question about `text`."""
    require_local(url)
    body = json.dumps(
        {
            "model": model,
            "state": {"text": text},
            "questions": {k: {"type": "noul", "instructions": q} for k, q in questions.items()},
        }
    ).encode()
    for attempt in range(retries + 1):
        req = urllib.request.Request(f"{url}/v1/systemone", body, {"content-type": "application/json"})
        try:
            with _post(req, timeout=300) as r:
                answers = json.load(r)["answers"]
            out = {}
            for k in questions:
                p = answers.get(k, {}).get("noul")
                if not isinstance(p, (int, float)) or not 0 <= p <= 1:
                    raise JeffError(f"malformed answer for {k!r}: {answers.get(k)!r}")
                out[k] = float(p)
            return out
        except urllib.error.HTTPError as e:
            if e.code == 529 and attempt < retries:
                time.sleep(float(e.headers.get("Retry-After", "1") or 1))
                continue
            raise JeffError(f"Jeff answered HTTP {e.code}") from e
        except TimeoutError:
            # the GPU may be shared with other apps: a slow answer is retried, not fatal
            if attempt < retries:
                time.sleep(5)
                continue
            raise JeffError(f"Jeff timed out {retries + 1} times; is something else using the GPU?") from None
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError) and attempt < retries:
                time.sleep(5)
                continue
            raise JeffError(f"Jeff is not reachable at {url} ({e.reason}); see https://github.com/firelex/jeff") from e
    raise JeffError("Jeff stayed busy")


def health(url: str = DEFAULT_URL) -> dict:
    require_local(url)
    with _OPENER.open(f"{url}/health", timeout=5) as r:
        return json.load(r)
