"""Cross-module regression tests for shared utility duplication.

The memory, host, and common utility modules each carry their own copy of
slug-normalisation and remote-URL canonicalisation logic (they cannot share
one implementation because AES201 forbids utility→utility imports). These
tests assert that every copy produces identical output for the same edge-case
inputs, so a divergence in one copy is caught at test time.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ─── Bootstrap sys.path (mirrors modules/root_sdc_entry.py) ─────────────
_MODULES_ROOT = Path(__file__).resolve().parents[3]
for _m in ("shared", "cli", "planner", "memory"):
    _src = _MODULES_ROOT / _m / "src"
    if _src.is_dir():
        _p = str(_src)
        if _p not in sys.path:
            sys.path.insert(0, _p)
if str(_MODULES_ROOT) not in sys.path:
    sys.path.insert(0, str(_MODULES_ROOT))

from shared.src.common.utility_sdc_common import bootstrap_ns_roots

bootstrap_ns_roots()

import pytest  # noqa: E402

from shared.src.common import utility_sdc_common as common  # noqa: E402
from shared.src.host import utility_host_helper as host  # noqa: E402
from shared.src.memory import utility_memory_helper as mem  # noqa: E402


# ─── Shared edge-case inputs ───────────────────────────────────────────

REMOTE_URLS = [
    "https://github.com/User/My-Repo.git",
    "git@github.com:user/my-repo.git",
    "github.com:user/my-repo",
    "ssh://git@github.com/user/my-repo.git",
    "https://github.com/user/repo.git.git",
    "https://github.com/user/simple",
    "https://gitlab.com/User/Repo.git",
    "https://bitbucket.org/team/service.git",
    "https://github.com/user/My_Repo",
]

SLUG_NAMES = [
    "My-Repo",
    "my_repo",
    "repo.git.git",
    "UPPER.Case-Name",
    "name with spaces",
    "a",
    "---",
    "Already-Slugged",
    "unicode-ñame",
    "",
]

SANITIZE_TEXTS = [
    "hello world",
    "line1\nline2",
    "tab\there",
    "  leading and trailing  ",
    "mixed\r\n\r\nnewlines",
]

NORMALIZE_TEXTS = [
    "Hello World.",
    "hello, world!",
    "  spaced   out  ",
    "ends.with.dots...",
    "UPPER CASE",
]


# ─── Slugify consistency ───────────────────────────────────────────────


class TestSlugifyConsistency:
    """Every slugify copy must produce the same output for the same input."""

    @pytest.mark.parametrize("name", SLUG_NAMES)
    def test_slugify_matches_common(self, name):
        expected = common.slugify(name)
        assert host._slugify(name) == expected
        assert mem._slugify(name) == expected


# ─── Canonicalize remote consistency ───────────────────────────────────


class TestCanonicalizeRemoteConsistency:
    """Every canonicalise copy must produce the same output for the same input."""

    @pytest.mark.parametrize("url", REMOTE_URLS)
    def test_canonicalize_matches_common(self, url):
        expected = common.canonicalize_remote(url)
        assert mem._canonicalize_remote(url) == expected


# ─── Sanitize-one-line consistency ─────────────────────────────────────


class TestSanitizeOneLineConsistency:
    """Every sanitize-one-line copy must produce the same output."""

    @pytest.mark.parametrize("text", SANITIZE_TEXTS)
    def test_sanitize_matches_common(self, text):
        expected = common.sanitize_one_line(text)
        assert mem._sanitize_one_line(text) == expected


# ─── Normalize consistency ─────────────────────────────────────────────


class TestNormalizeConsistency:
    """Every normalize copy must produce the same output."""

    @pytest.mark.parametrize("text", NORMALIZE_TEXTS)
    def test_normalize_matches_common(self, text):
        expected = common.normalize(text)
        assert mem._normalize(text) == expected


# ─── Edge-case: double .git suffix ─────────────────────────────────────


class TestDoubleGitSuffix:
    """A URL ending in ``.git.git`` must strip both suffixes (→ ``foo``)."""

    @pytest.mark.parametrize(
        "url,expected_tail",
        [
            ("https://github.com/user/foo.git.git", "foo"),
            ("https://github.com/user/foo.git", "foo"),
        ],
    )
    def test_remote_name_strips_all_git_suffixes(self, url, expected_tail):
        assert common.repo_name_from_remote.__doc__  # sanity
        # The helper strips ``.git`` repeatedly; verify via canonicalize.
        canonical = common.canonicalize_remote(url)
        assert canonical.endswith(expected_tail)

    def test_memory_canonicalize_matches(self):
        url = "https://github.com/user/foo.git.git"
        assert mem._canonicalize_remote(url) == common.canonicalize_remote(url)