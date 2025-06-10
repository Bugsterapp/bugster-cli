default:
    @just --list

update-deps:
    @echo "🚧 Updating deps..."
    python scripts/update_dependencies.py
    @echo "✅ Done!"

# Release commands
release-dev version variant="beta":
    #!/usr/bin/env bash
    ./scripts/release.sh {{version}} development {{variant}}

release-prod version:
    #!/usr/bin/env bash
    ./scripts/release.sh {{version}} production

release-interactive:
    #!/usr/bin/env bash
    ./scripts/interactive-release.py

release version type number:
    #!/usr/bin/env bash
    if [ "{{type}}" = "stable" ]; then
        TAG="v{{version}}"
    else
        TAG="v{{version}}-beta.{{number}}"
    fi
    echo "🚀 Releasing... $TAG"
    git tag -a "$TAG" -m "Bugster CLI $TAG" && git push origin --tags
    echo "✅ Done!"
