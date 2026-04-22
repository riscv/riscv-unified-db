# bin/.mise.sh — sourced by all bin/ wrappers to ensure mise is on PATH.
#
# If mise is already on PATH, do nothing. If not, look for the standard
# user-local install location and prepend it to PATH for this process only.
#
# This makes bin/ wrappers self-contained: they work immediately after
# bin/setup even if the user has not yet added "mise activate" to their
# shell profile.

if ! command -v mise &>/dev/null; then
  if [[ -x "${HOME}/.local/bin/mise" ]]; then
    export PATH="${HOME}/.local/bin:${PATH}"
  else
    printf "error: mise not found. Run bin/setup or see https://mise.jdx.dev/getting-started.html\n" >&2
    exit 1
  fi
fi
