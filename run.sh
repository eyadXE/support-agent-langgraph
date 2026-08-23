#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
case "${1:-help}" in
  api)  uvicorn app.app_run:app --reload ;;
  eval) python3 -m app.evals.run_eval ;;
  *) echo "Usage: ./run.sh {api|eval}" ;;
esac
