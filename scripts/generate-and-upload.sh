#!/usr/bin/env bash
# Generate the STAC catalog and (optionally) upload it to R2.
#
# By default this does a dry run: generate the catalog into a temp dir and
# print the files that would be uploaded. Pass --commit to actually upload.
#
# Upload requires R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY in
# the environment. Pass --op-env to load them from 1Password via `op run`.

set -euo pipefail

cd "$(dirname "$0")/.."

# If --op-env is present, re-exec under `op run` with R2_* injected from
# 1Password. The R2 creds live in the `r2-stac-rw` item in the Dynamical vault.
if [[ " $* " == *" --op-env "* ]]; then
  filtered=()
  for arg in "$@"; do
    [[ "$arg" != "--op-env" ]] && filtered+=("$arg")
  done
  exec op run --env-file=<(cat <<'EOF'
R2_ENDPOINT_URL=op://Dynamical/r2-stac-rw/Endpoint
R2_ACCESS_KEY_ID=op://Dynamical/r2-stac-rw/Access Key ID
R2_SECRET_ACCESS_KEY=op://Dynamical/r2-stac-rw/Secret Access Key
EOF
) -- "$0" ${filtered[@]+"${filtered[@]}"}
fi

commit=false
for arg in "$@"; do
  case "$arg" in
    --commit) commit=true ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

uv sync

if $commit; then
  : "${R2_ENDPOINT_URL:?must be set}"
  : "${R2_ACCESS_KEY_ID:?must be set}"
  : "${R2_SECRET_ACCESS_KEY:?must be set}"
  uv run python src/__main__.py generate-and-upload
else
  out=$(mktemp -d)
  trap 'rm -rf "$out"' EXIT
  uv run python src/__main__.py generate --output "$out"
  echo
  echo "Dry run — would upload the following to R2:"
  (cd "$out" && find . -name '*.json' | sort | sed 's|^\./||')
  echo
  echo "Re-run with --commit to upload."
fi
