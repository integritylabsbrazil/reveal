# AGENTS.md — Instruções para Agentes

Este documento define como agentes de IA devem interagir com o usuário e processar a documentação e implementação de tickets neste projeto.

---

## 1. Estrutura do Projeto

```
reveal/
├── .gitignore
├── LICENSE
├── AGENTS.md
├── README.md
├── refine-config.json            ← Configuração (Jira, projetos)
├── refine-ticket.sh              ← Orquestrador principal
├── create-ticket-doc.sh          ← Script de fetch Jira (legado)
├── generate-context.sh           ← Gera contexto-implementacao.md
├── generate-index.sh             ← Regenera INDEX.md
├── validate-ticket.sh            ← Valida consistência entre docs
│
├── lib/
│   ├── jira-fetch.sh             ← Deep fetch Jira
│   ├── code-scan.sh              ← Scan de código multi-linguagem
│   ├── generate-questions.sh     ← Perguntas para o negócio
│   └── generate-refinement.sh    ← Refinamento técnico
│
├── templates/
│   ├── perguntas-negocio-template.md
│   └── refinamento-tecnico-template.md
│
├── hooks/
│   └── commit-msg                ← Hook para validar mensagens
│
└── tickets/                      ← Documentação de tickets (criada pelo refine)
    ├── _template/                ← Modelo para novos tickets
    └── INDEX.md                  ← Índice gerado

# Projetos de código fonte (fora deste repo):
# ../projetos/meu-projeto-backend/
# ../projetos/meu-projeto-frontend/
```

---

## 2. Variáveis de Ambiente

| Variável | Obrigatória? | Descrição |
|----------|-------------|-----------|
| `JIRA_USER` | Sim (para fetch) | Email ou usuário Jira |
| `JIRA_TOKEN` | Sim (para fetch) | Token de API do Jira |
| `JIRA_BASE` | Sim (para fetch) | URL base do Jira (ex: https://meujira.atlassian.net) |

> Se não estiverem em env vars, o script tentará ler de `~/.jira-credentials` (formato: `usuario:token`).

---

## 3. Descoberta de Contexto

O agente pode estar em três situações em relação à estrutura do projeto:

| Situação | Como encontrar `tickets/` | Como encontrar projetos |
|----------|---------------------------|------------------------|
| Na raiz do refine-ticket | `./tickets/` | `../projetos/` |
| Dentro de tickets/ | `./` | `../../projetos/` |
| Dentro de projetos/ | `../../tickets/` | `./` |

**Regra geral:** O diretório raiz do reveal contém `refine-ticket.sh`.

---

## 4. Fluxo de Perguntas — AO INICIAR UMA SESSÃO

### Passo 1: Descubra o contexto e tickets com tarefas pendentes

```bash
find ./tickets -name "status-tasks.json" -exec grep -l '"pendente"' {} \;
```

### Passo 2: Identifique tickets disponíveis

Liste tickets com tarefas pendentes no projeto atual.

### Passo 3: Pergunte qual ticket

```
Qual ticket você vai trabalhar? (ex: PROJ-123)
```

### Passo 4: Pergunte o que fazer

```
O que você quer fazer?

[📋] a) Gerar documentação — Buscar dados do Jira e criar planos + subtarefas
[⚙️] b) Implementar uma task — Executar uma subtarefa específica
[📊] c) Verificar status — Mostrar progresso do ticket e subtarefas
```

---

## 5. Geração da Documentação

### 5.1. Analise o código fonte

Para cada projeto identificado como afetado:
- Leia `settings.gradle` / `pom.xml` / `package.json` (multi-module?)
- Mapeie pacotes com `ls src/main/java/...` ou `ls src/`
- Identifique padrões de implementação em tickets similares

### 5.2. Gere os arquivos base

1. **`description.md`**: Conteúdo do Jira enriquecido com análise de negócio
2. **`implementation-plan.md`**: Abordagem técnica, riscos, cronograma
3. **`roteiro-demo.md`**: Script de apresentação para o negócio
4. **`demo-artifacts/`**: Artefatos da demonstração (Postman, SQL)

### 5.3. Gere as subtarefas → `status-tasks.json`

Cada subtarefa deve ser:
- **Atômica**: faz uma coisa só (criar classe, alterar método, escrever testes)
- **Executável**: descrição clara do que precisa ser feito
- **Validável**: compila, testa, pode ser verificada
- **Associada a um projeto**: especifica em qual projeto implementar

Exemplo de `status-tasks.json`:

```json
{
  "ticketId": "PROJ-123",
  "ultimaAtualizacao": "2026-01-01T00:00:00",
  "projetosEnvolvidos": [
    "meu-projeto-backend"
  ],
  "tarefas": [
    {
      "id": "0001",
      "projeto": "meu-projeto-backend",
      "descricao": "Criar interface de servico para nova funcionalidade",
      "caminhoProjeto": "../projetos/meu-projeto-backend",
      "tipo": "criar-classe",
      "dependeDe": [],
      "bloqueadoPor": null,
      "status": "pendente"
    },
    {
      "id": "0002",
      "projeto": "meu-projeto-backend",
      "descricao": "Implementar classe concreta do servico com regras de negocio",
      "caminhoProjeto": "../projetos/meu-projeto-backend",
      "tipo": "criar-classe",
      "dependeDe": ["0001"],
      "bloqueadoPor": null,
      "status": "pendente"
    },
    {
      "id": "0003",
      "projeto": "meu-projeto-backend",
      "descricao": "Criar endpoint REST para expor a funcionalidade",
      "caminhoProjeto": "../projetos/meu-projeto-backend",
      "tipo": "adicionar-endpoint",
      "dependeDe": ["0002"],
      "bloqueadoPor": null,
      "status": "pendente"
    },
    {
      "id": "0004",
      "projeto": "meu-projeto-backend",
      "descricao": "Escrever testes unitarios para servico e endpoint",
      "caminhoProjeto": "../projetos/meu-projeto-backend",
      "tipo": "testes-unitarios",
      "dependeDe": ["0001", "0003"],
      "bloqueadoPor": null,
      "status": "pendente"
    },
    {
      "id": "0005",
      "projeto": "meu-projeto-backend",
      "descricao": "Preparar roteiro de demo e collection Postman para apresentacao",
      "caminhoProjeto": "../projetos/meu-projeto-backend",
      "tipo": "demo",
      "dependeDe": ["0003"],
      "bloqueadoPor": null,
      "status": "pendente",
      "artefatos": ["roteiro-demo.md", "postman-collection.json", "postman-environment.json", "queries.sql"]
    }
  ]
}
```

### 5.4. Gere `contexto-implementacao.md`

Resumo visual com tabela de subtarefas, dependências e projetos afetados.

> **O estado real está no `status-tasks.json`.** O `contexto-implementacao.md` é apenas um resumo visual gerado via `generate-context.sh`.

---

## 6. Ciclo de Vida de uma Task

Cada task segue este ciclo. Todas as tasks de um ticket ficam na mesma branch (`feature/PROJ-X`). Ao final de cada task, os commits intermediários são squashed em UM commit da task.

```
  pendente
      │ "implemente a task 0001"
      ▼
  em_andamento ← Marcar no JSON
      │
      ├─ 1. Instalar pre-commit hook (se não existir)
      ├─ 2. Implementar código no projeto
      ├─ 3. Compilar e rodar testes
      ├─ 4. Verificar lints/checks
      │
      ▼
  Auto-detecção de alterações
  git diff --name-only
      │
      ├── Se alterações inesperadas → perguntar: "Desfazer?"
      │
      ▼
  Squash dos commits intermediários
  git reset --soft HEAD~N
  git commit -m "PROJ-X-0001: descricao"
      │
      ▼
  Registrar no JSON:
  "status": "concluido"
  "commitHash": "abc1234"
  "rollbackCommand": "git revert abc1234 --no-edit"
      │
      ▼
  Perguntar: "Task 0001 concluída. Ir para a 0002?"
```

### 6.1. Pré-commit Hook

Na primeira task de cada sessão, instale o hook no projeto:

```bash
cp "$PWD/hooks/commit-msg" ".git/hooks/commit-msg"
```

Isso garante que mensagens de commit sigam o padrão `PROJ-X-NNNN: descricao`.

### 6.2. Auto-detecção de Arquivos Inesperados

```bash
git diff --name-only HEAD
```

Regra prática: uma task do tipo `criar-classe` só deve CRIAR arquivos novos. Uma task `alterar-classe` só deve MODIFICAR arquivos existentes.

### 6.3. Registro no JSON após conclusão

```json
{
  "id": "0001",
  "status": "concluido",
  "validacoes": { "compilou": true, "testesPassaram": true, "lintOk": true },
  "commitHash": "abc1234def567",
  "rollbackCommand": "git revert abc1234def567 --no-edit",
  "commitsIntermediarios": 3,
  "dataConclusao": "2026-01-01T22:00:00",
  "observacoes": "Implementado conforme especificacao"
}
```

### 6.4. Registro no JSON após falha

```json
{
  "id": "0002",
  "status": "falhou",
  "rollbackCommand": "git reset --hard HEAD~1",
  "motivoFalha": "Teste unitario nao passou apos 3 tentativas",
  "dataFalha": "2026-01-01T22:30:00"
}
```

---

## 7. Rollback por Task

```bash
# Ver hash
jq -r '.tarefas[] | select(.id == "0001") | .rollbackCommand' status-tasks.json

# Reverter
git revert <hash> --no-edit
```

Se a task não foi commitada ainda:

```bash
git checkout -- .
```

---

## 8. Múltiplos Tickets Ativos

```bash
find ./tickets -name "status-tasks.json" | while read f; do
  jq -r '.ticketId + ": " + (.tarefas | map(select(.status=="pendente")) | length | tostring) + " tarefas pendentes"' "$f"
done
```

Tasks podem ser executadas em qualquer ordem, desde que as dependências estejam satisfeitas.

---

## 9. Templates de Prompts por Tipo de Task

### 9.1. Tipo: `criar-classe`

```
1. Leia a implementação similar de referência
2. Crie a classe no pacote apropriado
3. Siga os padrões do projeto (anotações, extends, implements)
4. Crie testes unitários equivalentes
5. Compile e teste
```

### 9.2. Tipo: `adicionar-endpoint`

```
1. Identifique o Controller/FeignClient existente ou crie um novo
2. Adicione o método com a anotação @PostMapping/@GetMapping
3. Configure headers, timeout, retry conforme padrão do projeto
4. Teste com WireMock ou similar
```

### 9.3. Tipo: `testes-unitarios`

```
1. Localize a classe de teste existente ou crie uma nova
2. Use o mesmo framework de mock da base
3. Cubra: sucesso, erro de conexão, timeout, HTTP 4xx, HTTP 5xx
4. Siga o padrão de nomenclatura visto em outros testes
```

### 9.4. Tipo: `testes-integracao`

```
1. Configure ambiente de teste (WireMock, banco em memória, etc.)
2. Teste o fluxo completo: entrada → processamento → saída
3. Verifique logs, exceções, rollbacks
```

### 9.5. Tipo: `demo`

```
1. Gere o roteiro-demo.md com cenários de apresentação para o negócio
2. Crie a collection do Postman com requests organizados por cenário
3. Crie o environment do Postman com variáveis de ambiente
4. Crie queries SQL para demonstrar dados antes/depois
```

**Regra obrigatória — validação do body do request:**

Antes de definir o body de qualquer request na collection, você DEVE:
1. Localizar a classe DTO do request no código fonte
2. Ler todas as anotações de validação (`@NotBlank`, `@NotNull`, `@NotEmpty`, etc.)
3. Para cada campo obrigatório, incluir um valor de exemplo no body
4. Usar APENAS os campos e nomes definidos no DTO — nunca inventar campos

---

## 10. Sincronização JSON com MD

O agente SEMPRE:

1. **Lê** `status-tasks.json` primeiro (fonte da verdade)
2. **Executa** a ação
3. **Atualiza** `status-tasks.json` com o novo estado
4. **Sincroniza** `contexto-implementacao.md`

```bash
./generate-context.sh TICKET_ID
./validate-ticket.sh TICKET_ID
./generate-index.sh
```

---

## 11. Exemplo de Sessão Completa

```
Usuário: "gere documentacao para PROJ-123"
Agente:
├── refine-ticket.sh PROJ-123 --refine
├── Lê jira-data.json e analisa ../projetos/
├── Gera description.md, implementation-plan.md, roteiro-demo.md
├── Cria demo-artifacts/ (postman-collection, environment, queries)
├── Cria 5 subtarefas em status-tasks.json
├── Gera contexto-implementacao.md
└── "Documentacao criada com 5 tarefas."

Usuário: "implemente a task 0001 do PROJ-123"
Agente:
├── Lê status-tasks.json: 0001 pendente
├── Marca 0001 como "em_andamento"
├── Instala pre-commit hook
├── Cria interface e implementação
├── Compila e testa
├── Squash commits → git commit -m "PROJ-123-0001: Criar interface"
├── Marca 0001 como concluido
├── Atualiza contexto-implementacao.md
└── "Task 0001 concluida. Ir para a 0002?"
```

---

## 12. Squash Final para MR

Quando todas as tasks do ticket estiverem concluídas:

```bash
# Verificar commits
git log --oneline <base-branch>..HEAD

# Squash tudo em UM commit
git reset --soft <base-branch>
git commit -m "PROJ-X: Resumo do ticket"
```

> Cada commit de task fica preservado no histórico local até o squash. O `rollbackCommand` de cada task perde validade após o squash final.

---

## 13. Verificação Arquitetural (Checkbox Obrigatório)

- [ ] Li `settings.gradle`/`pom.xml`/`package.json` dos projetos
- [ ] Mapeei os pacotes de cada módulo
- [ ] Identifiquei corretamente a ordem de dependência entre módulos
- [ ] As subtarefas cobrem todos os projetos afetados
- [ ] Dependências entre subtarefas estão corretas

---

## 14. Verificação Cruzada de Documentos

- [ ] `status-tasks.json` reflete o estado real
- [ ] `contexto-implementacao.md` reflete o mesmo estado
- [ ] `INDEX.md` reflete progresso atualizado
- [ ] `implementation-plan.md` não referencia arquivos desatualizados
- [ ] `roteiro-demo.md` está alinhado com o estado real

---

## 15. Fluxo de Refinamento Técnico

### 15.1. Quando usar

- Tech lead recebeu ticket novo e quer preparar para o time dev
- Antes da planning/sprint
- Descrição do ticket é insuficiente ou vaga

### 15.2. Ferramenta

```bash
refine-ticket.sh PROJ-123 --refine
```

Pipeline:
1. **Deep Jira Fetch** → épico, links, subtasks, comentários, changelog
2. **Code Scan** → mapeia projetos, módulos, arquivos relevantes
3. **Perguntas** → analisa gaps e gera perguntas para o negócio
4. **Refinamento** → gera documento técnico completo

### 15.3. Configuração

```bash
export JIRA_USER="email@empresa.com"
export JIRA_TOKEN="seu-token"
export JIRA_BASE="https://meujira.atlassian.net"
```

Copie `refine-config.json` → `refine-config.local.json` e ajuste para seu projeto.

### 15.4. Fluxo de Uso

```
TECH LEAD:
1. ./refine-ticket.sh PROJ-123 --refine
2. Revisar perguntas-negocio.md
3. Enviar para o PO
4. Com respostas: refinar refinamento-tecnico.md
5. Gerar subtarefas em status-tasks.json
6. Repassar para o time dev
```

### 15.5. Documentos Gerados

| Arquivo | Conteúdo | Para quem |
|---------|----------|-----------|
| `jira-data.json` | Dados completos do Jira (épico, links, comentários) | Agente IA |
| `jira-summary.md` | Resumo legível do ticket | Tech lead |
| `impact-report.json` | Estrutura dos projetos de código | Agente IA |
| `perguntas-negocio.md` | Tabela de perguntas para o negócio | PO / Analista |
| `refinamento-tecnico.md` | Documento completo de refinamento | Time dev |

### 15.6. Exemplo de Perguntas Geradas

| # | Pergunta | Categoria | Impacto |
|---|----------|-----------|---------|
| 1 | Quais são os critérios de aceitação detalhados? | Especificação | Alto |
| 2 | Existe contrato/swagger da API de integração? | Integração | Alto |
| 3 | Em caso de timeout, qual o comportamento esperado? | Tratamento Erros | Alto |
| 4 | O toggle requer restart ou refresh em runtime? | Configuração | Médio |
| 5 | Dados pessoais precisam de criptografia? | Segurança | Médio |
| 6 | Esta história inclui preparação ou ativação no fluxo? | Escopo | Alto |

### 15.7. Customização

Para usar com qualquer Jira e qualquer projeto:

1. Copie `refine-config.json` → `refine-config.local.json`
2. Ajuste `jira.baseUrl` para sua instância
3. Ajuste `projects[].path` para seus projetos

```json
{
  "jira": {
    "baseUrl": "https://meuprojeto.atlassian.net",
    "projectPrefixes": ["PROJ", "TICKET"]
  },
  "projects": [
    {
      "name": "meu-backend",
      "path": "../projetos/meu-backend",
      "language": "java",
      "buildTool": "gradle"
    }
  ]
}
```
