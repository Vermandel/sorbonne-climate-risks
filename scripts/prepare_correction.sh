#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 2 ]]; then
  echo "Usage: $0 CHEMIN_DU_CORRIGE CHEMIN_CHIFFRE.gpg" >&2
  exit 2
fi
repo_root="$(git rev-parse --show-toplevel)"
source_file="$1"
encrypted_file="$2"
public_key="$repo_root/publication/psc-public-key.asc"
[[ -f "$source_file" ]] || { echo "Corrigé introuvable: $source_file" >&2; exit 1; }
[[ -f "$public_key" ]] || { echo "Clé publique PSC introuvable: $public_key" >&2; exit 1; }
mkdir -p "$(dirname "$encrypted_file")"
temporary_keyring="$(mktemp -d)"
trap 'rm -rf "$temporary_keyring"' EXIT
chmod 700 "$temporary_keyring"
gpg --homedir "$temporary_keyring" --batch --quiet --import "$public_key"
fingerprint="$(gpg --homedir "$temporary_keyring" --batch --with-colons --fingerprint | awk -F: '$1 == "fpr" { print $10; exit }')"
gpg --homedir "$temporary_keyring" --batch --yes --trust-model always --recipient "$fingerprint" --output "$encrypted_file" --encrypt "$source_file"
echo "Archive PSC créée: $encrypted_file"
