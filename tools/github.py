"""CLI: preview writes locally; --apply performs authorized GitHub changes."""
import argparse
import json
from pathlib import Path
import re
import sys

if __package__:
    from .github_api import Client, GitHubError, REPOSITORY, merge_pr, public_summary, validate_sha
else:
    from github_api import Client, GitHubError, REPOSITORY, merge_pr, public_summary, validate_sha


def positive(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("Expected a positive number")
    return number


def parser():
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("kind", choices=("issue", "pr"))
    root.add_argument("action", choices=("inspect", "create", "update", "merge"))
    root.add_argument("number", nargs="?", type=positive)
    root.add_argument("--title")
    root.add_argument("--body-file", type=Path)
    root.add_argument("--state", choices=("open", "closed"))
    root.add_argument("--head")
    root.add_argument("--draft", action="store_true")
    root.add_argument("--expected-sha")
    root.add_argument("--apply", action="store_true")
    return root


def prepare(args):
    if args.action != "create" and args.number is None:
        raise GitHubError("This action requires an issue/PR number")
    if args.action == "create" and args.number is not None:
        raise GitHubError("Create does not accept a number")
    if args.action == "merge" and args.kind != "pr":
        raise GitHubError("Only pull requests can be merged")
    if args.action == "inspect" and args.apply:
        raise GitHubError("Inspect is read-only")
    if args.action in {"inspect", "merge"} and any(
            (args.title is not None, args.body_file is not None, args.state, args.head, args.draft)):
        raise GitHubError("Content fields do not apply to inspect/merge")
    if args.expected_sha and args.action != "merge":
        raise GitHubError("--expected-sha is only for merge")
    if args.action == "merge":
        validate_sha(args.expected_sha)
    if args.action == "inspect":
        return None
    if args.action == "merge":
        return {"expected_sha": args.expected_sha, "merge_method": "squash"}
    body = {}
    if args.title is not None:
        if not args.title.strip():
            raise GitHubError("Title must not be empty")
        body["title"] = args.title.strip()
    if args.body_file:
        body["body"] = args.body_file.read_text(encoding="utf-8")
        if not body["body"].strip():
            raise GitHubError("Body file must not be empty")
    if args.action == "create":
        if "title" not in body or "body" not in body:
            raise GitHubError("Create requires --title and --body-file")
        if args.state:
            raise GitHubError("New issues/PRs are created open")
        if args.kind == "pr":
            if (not args.head or args.head == "main" or not re.fullmatch(r"[A-Za-z0-9_./-]+", args.head)
                    or ".." in args.head or args.head.startswith(('/', '-'))):
                raise GitHubError("PR requires a valid local feature branch via --head")
            body.update(head=args.head, base="main", draft=args.draft)
        elif args.head or args.draft:
            raise GitHubError("Issue creation does not accept PR options")
    else:
        if args.head or args.draft:
            raise GitHubError("Update does not change head or draft state")
        if args.state:
            body["state"] = args.state
        if not body:
            raise GitHubError("Update requires at least one content/state field")
    return body


def execute(args, client_factory=Client):
    body = prepare(args)
    if args.action != "inspect" and not args.apply:
        return {"preview": True, "repository": REPOSITORY, "kind": args.kind,
                "action": args.action, "number": args.number, "changes": body}
    client = client_factory()
    client.verify_repository()
    endpoint = "issues" if args.kind == "issue" else "pulls"
    path = f"{endpoint}/{args.number}"
    if args.action == "merge":
        return merge_pr(client, args.number, args.expected_sha)
    if args.action in {"inspect", "update"}:
        existing = client.request("GET", path)
        if args.kind == "issue" and "pull_request" in existing:
            raise GitHubError("This number identifies a PR, not an issue")
        if args.action == "inspect":
            summary = public_summary(existing)
            if args.kind == "pr":
                summary["head_sha"] = existing.get("head", {}).get("sha")
            return summary
        client.request("PATCH", path, body)
        after = client.request("GET", path)
    else:
        created = client.request("POST", endpoint, body)
        number = created.get("number")
        if not isinstance(number, int) or number < 1:
            raise GitHubError("Create result cannot be verified; inspect before retrying")
        after = client.request("GET", f"{endpoint}/{number}")
    for field in ("title", "body", "state", "draft"):
        if field in body and after.get(field) != body[field]:
            raise GitHubError("GitHub did not confirm the requested fields; inspect before retrying")
    if args.kind == "pr" and args.action == "create":
        if after.get("head", {}).get("ref") != body["head"] or after.get("base", {}).get("ref") != "main":
            raise GitHubError("GitHub did not confirm the requested branches")
    return public_summary(after)


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        print(json.dumps(execute(args), ensure_ascii=False, indent=2))
        return 0
    except GitHubError as error:
        print(str(error), file=sys.stderr)
        return 1
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        # Never dump a raw exception which could include HTTP bodies or credentials.
        print("Invalid input or response; inspect current state before retrying", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
