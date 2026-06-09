#!/bin/bash
# lib/utils.sh — Shared utility functions for reveal tooling
# Source this file from any script that needs logging/colors.
# Set LOG_PREFIX before sourcing for context-specific messages.

RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
NC='\033[0m'

: "${LOG_PREFIX:=TOOL}"

log_info()    { echo -e "${BLUE}[${LOG_PREFIX}]${NC} $1" >&2; }
log_ok()      { echo -e "${GREEN}[${LOG_PREFIX}]${NC} $1" >&2; }
log_warn()    { echo -e "${YELLOW}[${LOG_PREFIX}]${NC} $1" >&2; }
log_error()   { echo -e "${RED}[${LOG_PREFIX}]${NC} $1" >&2; }
log_section() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════${NC}"
    echo ""
}
