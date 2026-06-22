#!/usr/bin/env bash
set -euo pipefail

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"

curl -sS -X POST "${API_BASE_URL}/inventory" \
  -H 'content-type: application/json' \
  -d '{"sku":"GUMMY-001","name":"Sour Gummy Worms","quantity":8,"reorder_threshold":10,"vendor":"Acme Candy Supply"}'

echo
sleep 5

curl -sS "${API_BASE_URL}/inventory/GUMMY-001"
echo

curl -sS "${API_BASE_URL}/alerts"
echo

curl -sS -X POST "${API_BASE_URL}/inventory" \
  -H 'content-type: application/json' \
  -d '{"sku":"GUMMY-001","name":"Sour Gummy Worms","quantity":40,"reorder_threshold":10,"vendor":"Acme Candy Supply"}'

echo
sleep 5

curl -sS "${API_BASE_URL}/alerts"
echo
