# Claude Code automation for PropMS.
#
# Two triggers:
#   1. @claude mentions in issues/PR comments — ad hoc "fix this" requests.
#   2. A nightly scheduled sweep — Claude checks for failing tests, fixes
#      what it can, and opens a PR. Remove the schedule job if you'd
#      rather trigger this manually at first.
#
# Setup required before this works:
#   - Run `/install-github-app` from Claude Code in this repo, or install
#     https://github.com/apps/claude manually (needs Contents, Issues,
#     Pull requests: read & write).
#   - Add ANTHROPIC_API_KEY as a repository secret.

name: Claude Code Automation

on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  schedule:
    - cron: "0 3 * * *"   # 03:00 UTC nightly — adjust or remove

jobs:
  respond-to-mentions:
    if: github.event_name != 'schedule'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
      issues: write
    steps:
      - uses: actions/checkout@v4

      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          # Responds to @claude mentions in issue/PR comments automatically.
          # CLAUDE.md in this repo drives conventions (branch names, commit
          # style, PR target).

  nightly-fix-sweep:
    if: github.event_name == 'schedule'
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          prompt: |
            Run the PropMS test suite (see CLAUDE.md for how). If everything
            passes, do nothing and exit. If there are failing tests, pick
            the smallest coherent set of related failures, fix them,
            add or update tests to cover the fix, create a branch following
            the fix/<description> convention, commit with a conventional
            commit message, and open a PR against develop with a clear
            description of root cause and fix. Do not attempt to fix
            everything in one PR — one focused PR per underlying issue.
          claude_args: "--max-turns 30"
