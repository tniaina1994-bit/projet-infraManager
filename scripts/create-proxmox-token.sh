#!/usr/bin/env bash
# Création d'un API token Proxmox pour InfraManager — testé sur Proxmox VE 9.1.
#
# Pièges Proxmox 9.1 : la création n'est PAS sur /access/token mais sur
#   POST /api2/json/access/users/{userid}/token/{tokenid}
# et le header d'auth s'écrit CSRFPreventionToken (pas CSRFProtection).
#
# Usage:
#   PVE_PASSWORD=xxx ./scripts/create-proxmox-token.sh [pve_url] [userid] [tokenid]
#   ou sans PVE_PASSWORD : le mot de passe est demandé (saisie masquée).
set -euo pipefail

PVE_URL=${1:-https://192.168.10.90:8006}
USERID=${2:-root@pam}
TOKENID=${3:-inframanager}

if [ -z "${PVE_PASSWORD:-}" ]; then
  read -rsp "Mot de passe $USERID: " PVE_PASSWORD
  echo
fi

py() { python3 -c "$1"; }

# 1) ticket de session
RESP=$(curl -sk -m 15 -X POST "$PVE_URL/api2/json/access/ticket" \
  --data-urlencode "username=$USERID" --data-urlencode "password=$PVE_PASSWORD")
TICKET=$(printf '%s' "$RESP" | py "import sys,json;print(json.load(sys.stdin)['data']['ticket'])") || {
  echo "Échec d'authentification sur $PVE_URL" >&2
  exit 1
}
CSRF=$(printf '%s' "$RESP" | py "import sys,json;print(json.load(sys.stdin)['data']['CSRFPreventionToken'])")

# 2) création du token
USER_ENC=$(printf '%s' "$USERID" | py "import urllib.parse,sys;print(urllib.parse.quote(sys.stdin.read().strip(),safe=''))")
OUT=$(curl -sk -m 15 -X POST "$PVE_URL/api2/json/access/users/$USER_ENC/token/$TOKENID" \
  -H "CSRFPreventionToken: $CSRF" -H "Cookie: PVEAuthCookie=$TICKET" \
  --data-urlencode "privsep=0")

SECRET=$(printf '%s' "$OUT" | py "
import sys, json
d = json.load(sys.stdin).get('data') or {}
print(d.get('value') or (d if isinstance(d, str) else ''))" 2>/dev/null || true)

if [ -z "$SECRET" ]; then
  MSG=$(printf '%s' "$OUT" | py "import sys,json;print(json.load(sys.stdin).get('message',''))" 2>/dev/null || printf '%s' "$OUT")
  echo "Échec de la création du token : $MSG" >&2
  echo "(si le token existe déjà, réutilise sa clé secrète — Proxmox ne la montre plus jamais)" >&2
  exit 1
fi

echo "Token créé : $USERID!$TOKENID"
echo "Ajouter dans .env :"
echo "  PROXMOX_TOKEN_ID=$USERID!$TOKENID"
echo "  PROXMOX_TOKEN_SECRET=$SECRET"
