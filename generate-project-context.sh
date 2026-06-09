#!/bin/bash
# generate-project-context.sh
# Gera projects-context/<projeto>.md a partir do codigo fonte.
# Uso: ./generate-project-context.sh <projeto>
#      ./generate-project-context.sh <projeto> --path <caminho>
#      ./generate-project-context.sh --all

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"
PROJECTS_DIR="$SCRIPT_DIR/projects-context"
CONFIG_FILE="${CONFIG_FILE:-$SCRIPT_DIR/refine-config.local.json}"

if [[ ! -f "$CONFIG_FILE" ]]; then
    CONFIG_FILE="$SCRIPT_DIR/refine-config.json"
fi

usage() {
    cat <<EOF
Uso: $0 <nome-projeto> [--path <caminho>]
     $0 --all

Argumentos:
  <nome-projeto>     Nome do projeto (deve estar no refine-config*.json)
  --path <caminho>   Caminho do projeto (opcional, se nao usar config)
  --all              Gera contexto para todos os projetos da config

EOF
    exit 0
}

generate() {
    local name="$1"
    local path="$2"
    local lang="${3:-java}"
    local build="${4:-}"

    echo "[PROJECT-CTX] Gerando contexto para $name ($path)"
    python3 "$LIB_DIR/extract_project_context.py" \
        --name "$name" \
        --path "$path" \
        --output "$PROJECTS_DIR" \
        --language "$lang" \
        --build-tool "$build"
    echo "[PROJECT-CTX] Concluido: $PROJECTS_DIR/$name.md"
}

if [[ $# -eq 0 ]]; then
    usage
fi

if [[ "$1" == "--all" ]]; then
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "ERRO: $CONFIG_FILE nao encontrado"
        exit 1
    fi
    echo "[PROJECT-CTX] Lendo projetos de $CONFIG_FILE"
    python3 -c "
import json, sys
with open('$CONFIG_FILE') as f:
    cfg = json.load(f)
for p in cfg.get('projects', []):
    print(f\"{p['name']}|{p['path']}|{p.get('language','java')}|{p.get('buildTool','')}\")
" | while IFS='|' read -r name path lang build; do
        generate "$name" "$SCRIPT_DIR/$path" "$lang" "$build"
    done
    echo "[PROJECT-CTX] Todos os contextos gerados em $PROJECTS_DIR/"
    exit 0
fi

NAME="$1"
shift

PATH_ARG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --path) PATH_ARG="$2"; shift 2 ;;
        --help|-h) usage ;;
        *) echo "Opcao desconhecida: $1"; usage ;;
    esac
done

if [[ -n "$PATH_ARG" ]]; then
    generate "$NAME" "$PATH_ARG"
    exit 0
fi

# Buscar na config
if [[ -f "$CONFIG_FILE" ]]; then
    python3 -c "
import json, sys
with open('$CONFIG_FILE') as f:
    cfg = json.load(f)
for p in cfg.get('projects', []):
    if p['name'] == '$NAME':
        print(f\"{p['path']}|{p.get('language','java')}|{p.get('buildTool','')}\")
        sys.exit(0)
print('NOT_FOUND')
" > /tmp/project_ctx_info.txt
    IFS='|' read -r cfg_path lang build < /tmp/project_ctx_info.txt
    if [[ "$cfg_path" != "NOT_FOUND" ]]; then
        generate "$NAME" "$SCRIPT_DIR/$cfg_path" "$lang" "$build"
        exit 0
    fi
fi

echo "ERRO: Projeto '$NAME' nao encontrado na config e nenhum --path fornecido"
echo "Projetos disponiveis na config:"
python3 -c "
import json
with open('$CONFIG_FILE') as f:
    cfg = json.load(f)
for p in cfg.get('projects', []):
    print(f'  {p[\"name\"]}')
" 2>/dev/null || true
exit 1
