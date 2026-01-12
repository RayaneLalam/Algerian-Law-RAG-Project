#!/bin/bash

# Model Pre-Download Wrapper Script
# Convenient way to run the model download script with proper setup

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/download_models.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Algerian Law RAG - Model Pre-Download Wrapper${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check if script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo -e "${RED}✗ Error: download_models.py not found at $PYTHON_SCRIPT${NC}"
    exit 1
fi

# Parse arguments
DEVICE="${1:-cpu}"
SKIP_QUANT="${2:-}"

# Validate device
if [[ "$DEVICE" != "cpu" && "$DEVICE" != "cuda" ]]; then
    echo -e "${RED}✗ Invalid device: $DEVICE (use 'cpu' or 'cuda')${NC}"
    echo -e "${YELLOW}Usage: $0 [cpu|cuda] [--skip-quantization]${NC}"
    exit 1
fi

# Show configuration
echo -e "\n${BLUE}Configuration:${NC}"
echo -e "  Device: ${GREEN}$DEVICE${NC}"
if [ -n "$SKIP_QUANT" ] && [ "$SKIP_QUANT" = "--skip-quantization" ]; then
    echo -e "  Skip quantization: ${GREEN}Yes${NC}"
fi

echo -e "\n${YELLOW}ℹ️  Models to download (~28GB total):${NC}"
echo -e "  • dangvantuan/sentence-camembert-large (~135MB)"
echo -e "  • sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (~90MB)"
echo -e "  • bofenghuang/vigogne-2-7b-chat (~14GB)"
echo -e "  • Qwen/Qwen2.5-7B-Instruct (~14GB)"

# Verify disk space
AVAILABLE_SPACE=$(df "$SCRIPT_DIR" | awk 'NR==2 {print $4}')
NEEDED_SPACE=$((28 * 1024 * 1024))  # 28GB in KB

if [ "$AVAILABLE_SPACE" -lt "$NEEDED_SPACE" ]; then
    echo -e "\n${RED}✗ Insufficient disk space${NC}"
    echo -e "  Available: $(numfmt --to=iec $((AVAILABLE_SPACE * 1024)) 2>/dev/null || echo "$AVAILABLE_SPACE KB")"
    echo -e "  Required: ~28GB"
    exit 1
fi

# Confirm before proceeding
echo -e "\n${YELLOW}This will download ~28GB of models. Continue? (y/n)${NC}"
read -r -p "> " response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Cancelled.${NC}"
    exit 0
fi

# Run the Python script
echo -e "\n${BLUE}Starting download...${NC}\n"

if [ -n "$SKIP_QUANT" ] && [ "$SKIP_QUANT" = "--skip-quantization" ]; then
    python "$PYTHON_SCRIPT" --device "$DEVICE" --skip-quantization
else
    python "$PYTHON_SCRIPT" --device "$DEVICE"
fi

EXIT_CODE=$?

# Print completion message
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✓ Download completed successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "\n${BLUE}Next steps:${NC}"
    echo -e "  1. Verify cache: ls -la $SCRIPT_DIR/cache/hub/"
    echo -e "  2. Run application: python $SCRIPT_DIR/run.py"
    echo -e "  3. Application will load models from cache automatically"
else
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}✗ Download failed with exit code $EXIT_CODE${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    exit $EXIT_CODE
fi
