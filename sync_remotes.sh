#!/bin/bash

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

# 1. Fetch from all remotes (live-swe-agent, mini-swe-agent, origin)
echo "Fetching latest changes from all remotes..."
git fetch --all

# Helper function to merge and handle conflicts
merge_remote() {
    REMOTE=$1
    BRANCH=$2
    
    echo ""
    echo ">>> Attempting to merge changes from $REMOTE/$BRANCH..."
    
    # Try to merge. If it fails (returns non-zero), we enter the 'else' block.
    if git merge "$REMOTE/$BRANCH"; then
        echo "✔ Success: $REMOTE/$BRANCH merged automatically."
    else
        echo ""
        echo "⚠️  CONFLICT DETECTED!"
        echo "Git has paused the merge so you can resolve the conflicts."
        echo ""
        echo "INSTRUCTIONS:"
        echo "1. Open the conflicting files (e.g. pyproject.toml)."
        echo "2. Fix the conflicts manually."
        echo "3. Run 'git add <file>'."
        echo "4. Run 'git commit' to finalize this merge."
        echo "5. Run this script AGAIN to proceed to the next remote."
        exit 1
    fi
}

# 2. Merge sequence
# Adjust 'main' if the remote branch is named 'master' or something else
merge_remote live-swe-agent main
merge_remote mini-swe-agent main

echo ""
echo "🎉 All remotes are up to date and merged!"
