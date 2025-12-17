#!/bin/bash

set -euo pipefail

# Ensure upstream remotes are configured
add_remote_if_missing() {
    REMOTE=$1
    URL=$2
    if ! git remote | grep -q "^${REMOTE}$"; then
        echo "Adding remote '$REMOTE' -> $URL"
        git remote add "$REMOTE" "$URL"
    fi
}

add_remote_if_missing live-swe-agent https://github.com/OpenAutoCoder/live-swe-agent.git
add_remote_if_missing mini-swe-agent https://github.com/SWE-agent/mini-swe-agent.git

MODE="fetch"
if [[ "${1:-}" == "--merge" ]]; then
    MODE="merge"
elif [[ -n "${1:-}" ]]; then
    echo "Usage: $0 [--merge]"
    echo "  (default)   fetch only"
    echo "  --merge     fetch, then merge upstream branches"
    exit 2
fi

# 1) Always fetch upstream branches. This never pushes anywhere.
echo "Fetching latest changes from all remotes..."
git fetch --all

echo ""
echo "✅ Fetch complete. Upstream branches are available as:"
echo "  - live-swe-agent/main"
echo "  - mini-swe-agent/main"

if [[ "$MODE" == "fetch" ]]; then
    echo ""
    echo "(Fetch-only mode) To merge, rerun: ./sync_remotes.sh --merge"
    exit 0
fi

# 2) Optional merge sequence
archive_upstream_readme() {
    REMOTE=$1
    BRANCH=$2

    local archive_path
    case "$REMOTE" in
        live-swe-agent) archive_path="README-live.md" ;;
        mini-swe-agent) archive_path="README-mini.md" ;;
        *) archive_path="README-${REMOTE}.md" ;;
    esac

    echo "Archiving $REMOTE/$BRANCH:README.md -> $archive_path"
    git show "$REMOTE/$BRANCH:README.md" > "$archive_path"
    git add "$archive_path"
}

merge_remote() {
    REMOTE=$1
    BRANCH=$2

    echo ""
    echo ">>> Attempting to merge changes from $REMOTE/$BRANCH..."

    if git merge --no-edit "$REMOTE/$BRANCH"; then
        echo "✔ Success: $REMOTE/$BRANCH merged."
        return 0
    fi

    echo ""
    echo "⚠️  CONFLICT DETECTED during merge of $REMOTE/$BRANCH"
    echo ""

    local conflicts
    conflicts=$(git diff --name-only --diff-filter=U || true)

    # Special-case: README conflicts are expected because swesh keeps its own
    # top-level README. We archive upstream README into README-live.md /
    # README-mini.md and keep swesh README.md.
    local allowlist
    allowlist="README.md"

    local can_auto=1
    for f in $conflicts; do
        if ! echo "$allowlist" | tr ' ' '\n' | grep -qx "$f"; then
            can_auto=0
            break
        fi
    done

    if [[ $can_auto -eq 1 ]]; then
        archive_upstream_readme "$REMOTE" "$BRANCH"
        git checkout --ours -- README.md
        git add README.md
        git commit --no-edit
        echo "✔ Success: $REMOTE/$BRANCH merged (upstream README archived)."
        return 0
    fi

    echo "Conflicts require manual resolution:"
    echo "$conflicts"
    echo ""
    echo "INSTRUCTIONS:"
    echo "1. Resolve files above."
    echo "2. Run 'git add <file>'."
    echo "3. Run 'git commit' to finalize this merge."
    echo "4. Rerun: ./sync_remotes.sh --merge"
    exit 1
}

merge_remote live-swe-agent main
merge_remote mini-swe-agent main

echo ""
echo "🎉 All upstream branches fetched and merged."
