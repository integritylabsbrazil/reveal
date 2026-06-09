# Bash completion for reveal scripts
# Load with: source completions.sh (or add to ~/.bashrc)

_reveal_complete() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local prev="${COMP_WORDS[$((COMP_CWORD - 1))]}"

    # Ticket ID at position 1 or after --config/--jira-base/--project-dir flags
    if [ "$COMP_CWORD" -eq 1 ] || [[ "$prev" =~ ^--(config|jira-base|project-dir)$ ]]; then
        local reveal_dir
        reveal_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd 2>/dev/null || echo ".")"
        local tickets_dir="$reveal_dir/tickets"
        if [ -d "$tickets_dir" ]; then
            local tickets
            tickets=$(ls -d "$tickets_dir"/[A-Z]*/ 2>/dev/null | sed 's|.*/tickets/||; s|/||')
            COMPREPLY=($(compgen -W "$tickets" -- "$cur"))
            return 0
        fi
    fi

    # Flags at position 2 (after ticket ID)
    local cmds="--help --refine --jira-deep --scan-impact --questions --refinement --plan --config --jira-base --project-dir"
    COMPREPLY=($(compgen -W "$cmds" -- "$cur"))
}

# register for all scripts
for cmd in gerar-documentacao.sh refine-ticket.sh validate-ticket.sh generate-context.sh setup.sh generate-index.sh; do
    complete -F _reveal_complete "$cmd" 2>/dev/null || true
done
