#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -f "$tmp_dir/source.txt" "$tmp_dir/target.txt" "$tmp_dir/bad.txt"; rmdir "$tmp_dir"' EXIT

cat > "$tmp_dir/source.txt" <<'EOF'
Visit https://example.com/running-shoes, contact test@example.com,
use 192.0.2.1:8080, 2001:db8::1 and MAC 00:1A:2B:3C:4D:5E.
Hello {name} %1$s <a href="https://example.com/running-shoes" data-id="sku-42"><b>world</b></a>.
{count, plural, one {# item} other {# items}}
EOF

cat > "$tmp_dir/target.txt" <<'EOF'
Besuchen Sie https://example.com/running-shoes, contact test@example.com,
nutzen Sie 192.0.2.1:8080, 2001:db8::1 und MAC 00:1A:2B:3C:4D:5E.
Hallo {name} %1$s <a href="https://example.com/running-shoes" data-id="sku-42"><b>Welt</b></a>.
{count, plural, one {# Artikel} other {# Artikel}}
EOF

uv run --no-project python "$repo_dir/scripts/validate_localization.py" \
  "$tmp_dir/source.txt" "$tmp_dir/target.txt"

sed 's/192\.0\.2\.1:8080/192,0,2,1 : 8080/' "$tmp_dir/target.txt" > "$tmp_dir/bad.txt"
if uv run --no-project python "$repo_dir/scripts/validate_localization.py" \
  "$tmp_dir/source.txt" "$tmp_dir/bad.txt"; then
  echo "validator accepted a modified IP address" >&2
  exit 1
fi

sed 's/data-id="sku-42"/data-id="sku-43"/' "$tmp_dir/target.txt" > "$tmp_dir/bad.txt"
if uv run --no-project python "$repo_dir/scripts/validate_localization.py" \
  "$tmp_dir/source.txt" "$tmp_dir/bad.txt"; then
  echo "validator accepted a modified frozen HTML attribute" >&2
  exit 1
fi

echo "validator tests passed"
