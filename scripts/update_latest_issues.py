import json
import os
import sys
import urllib.parse
import urllib.request

GITHUB_REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "")
GITHUB_ACTOR = os.environ.get("GITHUB_ACTOR", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
README_PATH = os.environ.get("README_PATH", "README.md")
ISSUES_COUNT = int(os.environ.get("ISSUES_COUNT", "5"))

START_MARKER = "<!-- LATEST_ISSUES_START -->"
END_MARKER = "<!-- LATEST_ISSUES_END -->"


def fetch_latest_issues(username: str, token: str, count: int):
    # 用 Search API 获取“该用户创建的 issue”，并按创建时间倒序
    # 注意：GitHub 的 issues 搜索结果里可能混入 PR，所以后面要过滤 pull_request
    query = f"author:{username} is:issue sort:created-desc"
    url = (
        "https://api.github.com/search/issues?q="
        + urllib.parse.quote(query)
        + f"&per_page={count * 2}"
    )

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "latest-issues-readme-updater",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    items = data.get("items", [])

    # 过滤掉 PR
    issues = [item for item in items if "pull_request" not in item]

    return issues[:count]


def build_markdown(issues):
    if not issues:
        return "- 暂无最近提交的 Issues"

    lines = []
    for issue in issues:
        title = issue["title"].replace("\n", " ").strip()
        url = issue["html_url"]
        repo_full_name = issue["repository_url"].replace("https://api.github.com/repos/", "")
        number = issue["number"]
        state = issue["state"]
        lines.append(f"- [{title}]({url}) · `{repo_full_name}#{number}` · `{state}`")
    return "\n".join(lines)


def update_readme(readme_path: str, new_block: str):
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    start = content.find(START_MARKER)
    end = content.find(END_MARKER)

    if start == -1 or end == -1 or start > end:
        raise RuntimeError("README 中没有找到占位符标记。")

    start += len(START_MARKER)
    updated = content[:start] + "\n" + new_block + "\n" + content[end:]

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated)


def main():
    if not GITHUB_ACTOR:
        print("缺少 GITHUB_ACTOR")
        sys.exit(1)

    if not GITHUB_TOKEN:
        print("缺少 GITHUB_TOKEN")
        sys.exit(1)

    issues = fetch_latest_issues(GITHUB_ACTOR, GITHUB_TOKEN, ISSUES_COUNT)
    markdown = build_markdown(issues)
    update_readme(README_PATH, markdown)
    print("README 已更新。")


if __name__ == "__main__":
    main()
