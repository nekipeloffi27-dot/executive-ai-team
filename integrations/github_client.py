"""GitHub API wrapper."""
from __future__ import annotations
from github import Github, Auth
from core.config import settings


_gh: Github | None = None


def get_gh() -> Github:
    global _gh
    if _gh is None:
        _gh = Github(auth=Auth.Token(settings.github_token))
    return _gh


def repo():
    return get_gh().get_repo(settings.product_repo)


def get_pr(number: int):
    return repo().get_pull(number)


def get_pr_diff(number: int) -> str:
    import httpx
    pr = get_pr(number)
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            pr.diff_url,
            headers={
                "Authorization": f"Bearer {settings.github_token}",
                "Accept": "application/vnd.github.v3.diff",
            },
        )
        return resp.text[:200_000]


def post_pr_comment(number: int, body: str) -> None:
    get_pr(number).create_issue_comment(body)
