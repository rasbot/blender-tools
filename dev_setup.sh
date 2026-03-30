#!/bin/bash
# Creates symlinks from a Blender addons directory to the local dev folders,
# so code changes are picked up on Reload Scripts (F3) without reinstalling.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
BLENDER_BASE="$APPDATA/Blender Foundation/Blender"
ADDONS=("vertex_measure" "mesh_tools")

if [ ! -d "$BLENDER_BASE" ]; then
    echo "Blender config directory not found at: $BLENDER_BASE"
    exit 1
fi

# List available versions
echo "Available Blender versions:"
versions=()
i=1
for dir in "$BLENDER_BASE"/*/; do
    ver=$(basename "$dir")
    versions+=("$ver")
    echo "  $i) $ver"
    ((i++))
done

if [ ${#versions[@]} -eq 0 ]; then
    echo "No Blender versions found."
    exit 1
fi

read -rp "Select version number: " choice
idx=$((choice - 1))

if [ $idx -lt 0 ] || [ $idx -ge ${#versions[@]} ]; then
    echo "Invalid selection."
    exit 1
fi

selected="${versions[$idx]}"
addons_dir="$BLENDER_BASE/$selected/scripts/addons"
mkdir -p "$addons_dir"

echo ""
for addon in "${ADDONS[@]}"; do
    target="$addons_dir/$addon"
    source="$REPO_DIR/$addon"

    if [ -L "$target" ]; then
        echo "  $addon: symlink already exists, skipping"
    elif [ -d "$target" ]; then
        echo "  $addon: directory already exists (installed copy?) — remove it first to use symlink"
    else
        cmd //c mklink //D "$(cygpath -w "$target")" "$(cygpath -w "$source")" > /dev/null 2>&1
        if [ -L "$target" ] || [ -d "$target" ]; then
            echo "  $addon: linked"
        else
            echo "  $addon: failed — try running as administrator"
        fi
    fi
done

echo ""
echo "Done. In Blender, press F3 and search 'Reload Scripts' to pick up changes."
