#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PY_VERSIONS=("3.10" "3.11" "3.12" "3.13" "3.14")
RUN_TESTS=1
RUN_COMPILEALL=1
SKIP_INSTALL=0

usage() {
  cat <<'EOF'
Usage:
  scripts/run_python_matrix.sh [options]

Options:
  --tests-only     Run unittest across Python 3.10/3.11/3.12/3.13/3.14
  --compileall-only
                   Run compileall across Python 3.10/3.11/3.12/3.13/3.14
  --skip-install   Reuse existing .venv-3.10 .. .venv-3.14 environments
  -h, --help       Show this help

Default:
  Create/update .venv-3.10 .. .venv-3.14, install the package, then run
  unittest discovery and compileall for each version.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tests-only)
      RUN_TESTS=1
      RUN_COMPILEALL=0
      ;;
    --compileall-only)
      RUN_TESTS=0
      RUN_COMPILEALL=1
      ;;
    --skip-install)
      SKIP_INSTALL=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

echo "==> Ensuring CPython interpreters are available"
uv python install "${PY_VERSIONS[@]}"

for py in "${PY_VERSIONS[@]}"; do
  venv=".venv-$py"
  pybin="$venv/bin/python"

  echo
  echo "==> Preparing environment for CPython $py"
  if [[ ! -x "$pybin" ]]; then
    uv venv "$venv" --python "$py"
  fi

  if [[ "$SKIP_INSTALL" -eq 0 ]]; then
    uv pip install -p "$pybin" -e .
  fi

  if [[ "$RUN_TESTS" -eq 1 ]]; then
    echo "==> [$py] unittest"
    "$pybin" -m unittest discover
  fi

  if [[ "$RUN_COMPILEALL" -eq 1 ]]; then
    echo "==> [$py] compileall"
    "$pybin" -m compileall dendro_text
  fi
done

echo
echo "Python matrix run completed."
