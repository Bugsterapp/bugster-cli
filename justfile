default:
    @just --list

update-deps:
    @echo "🚧 Updating deps..."
    python scripts/update_dependencies.py
    @echo "✅ Done!"

release version type:
    #!/usr/bin/env bash
    if [ "{{type}}" = "stable" ]; then
        TAG="v{{version}}"
    else
        TIMESTAMP=$(date +"%d%m%Y-%H%M")
        TAG="v{{version}}-beta-${TIMESTAMP}"
    fi
    echo "🚀 Releasing... $TAG"
    git tag -a "$TAG" -m "Bugster CLI $TAG" && git push origin --tags
    echo "✅ Done!"
