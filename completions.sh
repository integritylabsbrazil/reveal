# Bash completion for reveal scripts
# Load with: source completions.sh (or add to ~/.bashrc)

_reveal_tickets() {
    local cur="${COMP_WORDS[COMP_CWORD]}"
    local reveal_dir
    reveal_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd 2>/dev/null || echo ".")"
    local tickets_dir="$reveal_dir/tickets"

    if [ -d "$tickets_dir" ]; then
        local tickets
        tickets=$(ls -d "$tickets_dir"/[A-Z]*/ 2>/dev/null | sed 's|.*/tickets/||; s|/||')
        COMPREPLY=($(compgen -W "$tickets" -- "$cur"))
    fi
}

_reveal_commands() {
    local cur="${COMP_WORDS[1]}"
    local cmds="--help --refine --status --validate"
    COMPREPLY=($(compgen -W "$cmds" -- "$cur"))
}

# register completions for each script
for cmd in gerar-documentacao.sh refine-ticket.sh validate-ticket.sh generate-context.sh; do
    complete -F _reveal_tickets "$cmd" 2>/dev/null || true
done

# refine-ticket.sh also supports subcommands
complete -F _reveal_commands create-ticket-doc.sh 2>/dev/null || true
