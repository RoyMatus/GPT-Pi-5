"""Bounded GitHub operations for this repository only; no automatic write retries."""
import json
import os
import re
import subprocess
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

REPOSITORY = "RoyMatus/GPT-Pi-5"
BASE = f"https://api.github.com/repos/{REPOSITORY}"
EXPECTED_CHECKS = frozenset(
    f"test ({system}, {version})"
    for system in ("ubuntu-latest", "windows-latest")
    for version in ("3.11", "3.13")
)


class GitHubError(RuntimeError):
    """Safe, bounded error message without credentials or raw response bodies."""


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise GitHubError("GitHub redirect refused; verify repository identity")


def credential():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        result = subprocess.run(
            ["git", "credential", "fill"],
            input="protocol=https\nhost=github.com\n\n", capture_output=True,
            text=True, timeout=20,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"},
        )
    except (OSError, subprocess.TimeoutExpired):
        raise GitHubError("GitHub credentials unavailable") from None
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.startswith("password=") and line[9:]:
                return line[9:]
    raise GitHubError("Set GH_TOKEN/GITHUB_TOKEN or sign in through Git Credential Manager")


class Client:
    def __init__(self, token=None, opener=None):
        self._token = token
        self._opener = opener or build_opener(NoRedirect())

    def request(self, method, path="", body=None):
        # Endpoints are repository-relative. Never accept caller-provided hosts or traversal.
        parts = urlsplit(path)
        if (method not in {"GET", "POST", "PATCH", "PUT"} or parts.scheme or parts.netloc
                or path.startswith("/") or ".." in path or "%" in path or "\\" in path
                or parts.fragment or any(ord(c) < 32 for c in path)):
            raise GitHubError("Invalid repository-relative request")
        if self._token is None:
            self._token = credential()
        headers = {"Authorization": f"Bearer {self._token}",
                   "Accept": "application/vnd.github+json",
                   "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "GPT-Pi-5-tools"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(BASE + ("/" + path if path else ""), data=data,
                          headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=30) as response:
                raw = response.read(8 * 1024 * 1024 + 1)
                if len(raw) > 8 * 1024 * 1024:
                    raise GitHubError("GitHub response exceeds the supported size")
                return json.loads(raw) if raw else None
        except HTTPError as error:
            code = error.code
            error.close()
            raise GitHubError(f"GitHub HTTP {code}; inspect current state before retrying a write") from None
        except (URLError, TimeoutError, OSError, ValueError):
            raise GitHubError("GitHub response unavailable; inspect current state before retrying a write") from None

    def verify_repository(self):
        repo = self.request("GET")
        if repo.get("full_name") != REPOSITORY:
            raise GitHubError("Repository identity mismatch")
        return repo

    def collection(self, path, key):
        items = []
        separator = "&" if "?" in path else "?"
        for page in range(1, 101):
            result = self.request("GET", f"{path}{separator}per_page=100&page={page}")
            batch = result.get(key)
            if not isinstance(batch, list):
                raise GitHubError("Incomplete GitHub collection")
            items.extend(batch)
            total = result.get("total_count")
            if isinstance(total, int) and len(items) >= total:
                return items
            if len(batch) < 100:
                if isinstance(total, int) and len(items) < total:
                    raise GitHubError("Incomplete GitHub collection")
                return items
        raise GitHubError("GitHub pagination limit reached")


def validate_sha(sha):
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise GitHubError("Expected a full lowercase 40-character commit SHA")


def validate_pr(pr, expected_sha):
    validate_sha(expected_sha)
    if pr.get("base", {}).get("repo", {}).get("full_name") != REPOSITORY:
        raise GitHubError("PR repository mismatch")
    if pr.get("base", {}).get("ref") != "main":
        raise GitHubError("Merge target must be main")
    if pr.get("head", {}).get("sha") != expected_sha:
        raise GitHubError("PR head changed; inspect and verify the new commit")
    if pr.get("state") != "open" or pr.get("merged") or pr.get("draft"):
        raise GitHubError("PR must be open, unmerged and ready for review")
    if pr.get("mergeable") is not True or pr.get("mergeable_state") != "clean":
        raise GitHubError("PR mergeability is not clean or is still unknown")


def validate_checks(checks, statuses, sha):
    passed = set()
    for check in checks:
        if check.get("head_sha") != sha:
            raise GitHubError("Check result belongs to another commit")
        if check.get("status") != "completed" or check.get("conclusion") not in {"success", "neutral", "skipped"}:
            raise GitHubError("A check is pending or failed")
        if check.get("name") in EXPECTED_CHECKS:
            if check.get("app", {}).get("slug") != "github-actions" or check.get("conclusion") != "success":
                raise GitHubError("Required check did not succeed through GitHub Actions")
            passed.add(check["name"])
    if not EXPECTED_CHECKS <= passed:
        raise GitHubError("Required CI jobs are missing")
    if any(status.get("state") != "success" for status in statuses):
        raise GitHubError("A commit status is pending or failed")


def merge_pr(client, number, expected_sha):
    validate_sha(expected_sha)
    pr = client.request("GET", f"pulls/{number}")
    validate_pr(pr, expected_sha)
    # Query main itself: a PR base snapshot alone is not sufficient freshness evidence.
    base = client.request("GET", "git/ref/heads/main")["object"]["sha"]
    if pr["base"]["sha"] != base:
        raise GitHubError("PR base is stale")
    checks = client.collection(f"commits/{expected_sha}/check-runs?filter=latest", "check_runs")
    statuses = client.collection(f"commits/{expected_sha}/status", "statuses")
    validate_checks(checks, statuses, expected_sha)
    current = client.request("GET", f"pulls/{number}")
    validate_pr(current, expected_sha)
    fresh_base = client.request("GET", "git/ref/heads/main")["object"]["sha"]
    if fresh_base != base or current["base"]["sha"] != base:
        raise GitHubError("Main changed during verification; inspect and verify again")
    result = client.request("PUT", f"pulls/{number}/merge",
                            {"merge_method": "squash", "sha": expected_sha})
    if result.get("merged") is not True:
        raise GitHubError("GitHub did not confirm the merge")
    after = client.request("GET", f"pulls/{number}")
    if after.get("merged") is not True or after.get("head", {}).get("sha") != expected_sha:
        raise GitHubError("Merge result could not be verified; do not retry blindly")
    return {"repository": REPOSITORY, "number": number, "merged": True,
            "sha": result.get("sha"), "url": after.get("html_url")}


def public_summary(obj):
    fields = ("number", "title", "body", "state", "html_url", "draft", "merged", "mergeable_state")
    return {key: obj[key] for key in fields if key in obj}
