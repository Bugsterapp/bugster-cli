#!/bin/bash
# This script updates the version in __init__.py, creates a git tag, and pushes changes
# Usage: ./release.sh 0.1.8

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Help text
show_help() {
    echo "Bugster CLI Release Script"
    echo
    echo "Usage: $0 <version> <type> [variant]"
    echo
    echo "Arguments:"
    echo "  version     Version number (e.g., 1.2.3)"
    echo "  type        Either 'development' or 'production'"
    echo "  variant     Optional: 'alpha' or 'beta' (default: 'beta' for development)"
    echo
    echo "Examples:"
    echo "  $0 1.2.3 production     # Creates v1.2.3"
    echo "  $0 1.2.3 development    # Creates v1.2.3-beta.1"
    echo "  $0 1.2.3 development alpha  # Creates v1.2.3-alpha.1"
    echo
}

# Validate version format (x.y.z)
validate_version() {
    if ! [[ $1 =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        echo -e "${RED}Error: Invalid version format. Must be in format: x.y.z (e.g., 1.2.3)${NC}"
        exit 1
    fi
}

# Get the next available pre-release number
get_next_prerelease_number() {
    local version=$1
    local variant=$2
    local max_number=0
    
    # List all matching tags and find the highest number
    for tag in $(git tag -l "v${version}-${variant}.*"); do
        number=$(echo $tag | grep -oE "${variant}\.[0-9]+" | cut -d. -f2)
        if [ "$number" -gt "$max_number" ]; then
            max_number=$number
        fi
    done
    
    echo $((max_number + 1))
}

# Main script
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
    exit 0
fi

if [ "$#" -lt 2 ]; then
    echo -e "${RED}Error: Not enough arguments.${NC}"
    show_help
    exit 1
fi

VERSION=$1
TYPE=$2
VARIANT=${3:-beta}

# Validate inputs
validate_version "$VERSION"

if [ "$TYPE" != "development" ] && [ "$TYPE" != "production" ]; then
    echo -e "${RED}Error: Type must be either 'development' or 'production'${NC}"
    exit 1
fi

if [ "$TYPE" = "development" ] && [ "$VARIANT" != "beta" ] && [ "$VARIANT" != "alpha" ]; then
    echo -e "${RED}Error: Variant must be either 'alpha' or 'beta'${NC}"
    exit 1
fi

# Create tag based on type
if [ "$TYPE" = "production" ]; then
    TAG="v${VERSION}"
    if git tag -l "$TAG" | grep -q .; then
        echo -e "${RED}Error: Tag $TAG already exists${NC}"
        exit 1
    fi
else
    NEXT_NUMBER=$(get_next_prerelease_number "$VERSION" "$VARIANT")
    TAG="v${VERSION}-${VARIANT}.${NEXT_NUMBER}"
fi

# Show confirmation
echo -e "${YELLOW}Creating tag: ${TAG}${NC}"
echo -e "${YELLOW}This will trigger a GitHub Actions workflow to:${NC}"
if [ "$TYPE" = "production" ]; then
    echo -e "${GREEN}- Create a production release${NC}"
    echo -e "${GREEN}- Connect to api.bugster.app${NC}"
else
    echo -e "${GREEN}- Create a development pre-release${NC}"
    echo -e "${GREEN}- Connect to dev.bugster.api${NC}"
fi

# Ask for confirmation
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Aborted${NC}"
    exit 1
fi

# Create and push tag
echo -e "${YELLOW}Creating tag...${NC}"
git tag -a "$TAG" -m "Bugster CLI $TAG"
echo -e "${YELLOW}Pushing tag...${NC}"
git push origin "$TAG"

echo -e "${GREEN}✅ Successfully created and pushed tag: $TAG${NC}"

echo "=========================================="
echo "Release v$VERSION completed successfully"
echo "=========================================="
echo "GitHub Actions will now build and release the binaries"
echo "The release will be available at:"
echo "https://github.com/Bugsterapp/bugster-cli/releases/tag/v$VERSION"
echo "==========================================" 