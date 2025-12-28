#!/usr/bin/env bash
set -euo pipefail

# Build PSP package using FlavorPack
#
# Environment variables:
#   MANIFEST - Path to pyproject.toml
#   OUTPUT_PATH - Output .psp file location (optional)
#   PRIVATE_KEY - Path to Ed25519 private key (optional)
#   PUBLIC_KEY - Path to Ed25519 public key (optional)
#   KEY_SEED - Seed for deterministic key generation (optional)
#   STRIP - Strip debug symbols (true/false)
#   VERIFY - Verify package after build (true/false)

MANIFEST="${MANIFEST:-pyproject.toml}"
STRIP="${STRIP:-false}"
VERIFY="${VERIFY:-true}"

# Detect platform
OS_NAME=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case "${OS_NAME}" in
    linux) PLATFORM_OS="linux" ;;
    darwin) PLATFORM_OS="darwin" ;;
    *) PLATFORM_OS="${OS_NAME}" ;;
esac
case "${ARCH}" in
    x86_64|amd64) PLATFORM_ARCH="amd64" ;;
    aarch64|arm64) PLATFORM_ARCH="arm64" ;;
    *) PLATFORM_ARCH="${ARCH}" ;;
esac
PLATFORM="${PLATFORM_OS}_${PLATFORM_ARCH}"
echo "::notice::Building for platform: ${PLATFORM}"

# Build command
CMD="flavor pack --manifest ${MANIFEST}"

# Add output path if specified
if [[ -n "${OUTPUT_PATH:-}" ]]; then
    CMD="${CMD} --output ${OUTPUT_PATH}"
fi

# Add strip flag
if [[ "${STRIP}" == "true" ]]; then
    CMD="${CMD} --strip"
fi

# Add verify flag
if [[ "${VERIFY}" == "true" ]]; then
    CMD="${CMD} --verify"
else
    CMD="${CMD} --no-verify"
fi

# Handle signing keys
if [[ -n "${PRIVATE_KEY:-}" ]]; then
    CMD="${CMD} --private-key ${PRIVATE_KEY} --public-key ${PUBLIC_KEY}"
elif [[ -n "${KEY_SEED:-}" ]]; then
    CMD="${CMD} --key-seed ${KEY_SEED}"
else
    # Generate temporary keys
    echo "::group::Generating temporary signing keys"
    mkdir -p keys
    flavor keygen --out-dir keys
    CMD="${CMD} --private-key keys/flavor-private.key --public-key keys/flavor-public.key"
    echo "::endgroup::"
fi

# Execute build
echo "::group::Building PSP package"
echo "Command: ${CMD}"
eval "${CMD}"
echo "::endgroup::"

# Determine output path for GitHub output
if [[ -n "${OUTPUT_PATH:-}" ]]; then
    PSP_PATH="${OUTPUT_PATH}"
else
    # Extract package name from manifest
    NAME=$(grep '^name = ' "${MANIFEST}" | cut -d'"' -f2 || grep "^name = " "${MANIFEST}" | cut -d"'" -f2)
    PSP_PATH="dist/${NAME}.psp"
fi

echo "psp-path=${PSP_PATH}" >> "${GITHUB_OUTPUT}"
echo "platform=${PLATFORM}" >> "${GITHUB_OUTPUT}"
echo "::notice::Built PSP package: ${PSP_PATH} for ${PLATFORM}"
