#!/usr/bin/env bash

# icepick.sh
# Snapshot a repository into a single text file (structure + contents)

set -euo pipefail

OUTPUT="${1:-icepick_snapshot.txt}"
ROOT="${2:-.}"

echo "Creating snapshot of: $ROOT"
echo "Output file: $OUTPUT"

{
    echo "===== ICEPICK SNAPSHOT ====="
    echo "Generated: $(date)"
    echo "Root: $(cd "$ROOT" && pwd)"
    echo

    echo "===== DIRECTORY TREE ====="
    # Exclude common junk
    tree -a \
        -I '.git|node_modules|dist|build|__pycache__|*.pyc' \
        "$ROOT"
    echo

    echo "===== FILE CONTENTS ====="

    # Find all files (excluding junk), sorted for determinism
    find "$ROOT" -type f \
        ! -path "*/.git/*" \
        ! -path "*/node_modules/*" \
        ! -path "*/dist/*" \
        ! -path "*/build/*" \
        ! -name "*.pyc" \
        | sort \
        | while read -r file; do

            echo
            echo "----- FILE: $file -----"

            # Detect binary vs text
            if file "$file" | grep -q "text"; then
                cat "$file"
            else
                echo "[[ BINARY FILE SKIPPED ]]"
            fi

            echo
            echo "----- END FILE: $file -----"
            echo
        done

    echo "===== END SNAPSHOT ====="

} > "$OUTPUT"

echo "Snapshot complete."
