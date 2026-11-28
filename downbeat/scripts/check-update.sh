#!/bin/sh
# Reports whether the installed downbeat or its skill is out of date. Changes no files.
# Exit status: 0 up to date, 1 an update is needed.
set -u
minimum="0.2.0"
skill_dir="$(cd "$(dirname "$0")/.." && pwd -P)"
skills="$(git -C "$skill_dir" rev-parse --show-toplevel 2>/dev/null || true)"
repo="${DOWNBEAT_REPO:-$HOME/Developer/downbeat}"
state_dir="${DOWNBEAT_STATE_DIR:-$HOME/.local/share/downbeat}"
status=0

stale() {
    echo "update: $1"
    status=1
}

# Is a checkout behind the branch it follows?
behind() {
    [ -n "$1" ] && git -C "$1" rev-parse --git-dir >/dev/null 2>&1 || return 0
    if ! GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes -o ConnectTimeout=5" \
        git -C "$1" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=5 fetch --quiet 2>/dev/null; then
        echo "note: could not fetch $2, so it was compared with the last fetch"
    fi
    count="$(git -C "$1" rev-list --count 'HEAD..@{upstream}' 2>/dev/null || echo 0)"
    if [ "$count" -gt 0 ]; then stale "$2 is $count commit(s) behind. Run: git -C \"$1\" pull --ff-only"; fi
}

behind "$repo" downbeat
behind "$skills" skills

if [ -f "$repo/scripts/install.sh" ]; then
    install="\"$repo/scripts/install.sh\""
else
    install="the install steps in https://github.com/nvictor/downbeat"
fi

binary="${DOWNBEAT_BIN:-$(command -v downbeat || true)}"
if [ -z "$binary" ]; then
    stale "downbeat is not installed. Run: $install"
else
    version="$("$binary" --version 2>/dev/null || echo 0)"
    oldest="$(printf '%s\n%s\n' "$minimum" "$version" | sort -t . -k 1,1n -k 2,2n -k 3,3n | head -n 1)"
    if [ "$oldest" != "$minimum" ]; then
        stale "downbeat $version is older than $minimum, which this skill needs. Run: $install"
    elif [ -x "$repo/scripts/source-hash.sh" ]; then
        if [ "$("$repo/scripts/source-hash.sh")" != "$(cat "$state_dir/source-hash" 2>/dev/null)" ]; then
            stale "the installed binary does not match the source in $repo. Run: $install --no-pull"
        fi
    fi
fi

if [ "$status" -eq 0 ]; then echo "downbeat is up to date."; fi
exit "$status"
