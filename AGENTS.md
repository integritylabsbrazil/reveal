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
├── refine-ticket.sh              ← Orquestrador principal
├── gerar-documentacao.sh         ← Pipeline completo
├── setup.sh                      ← Setup interativo
├── generate-project-context.sh   ← Extrai contexto permanente do codigo fonte
├── refine-config.json            ← Configuração (Jira, projetos)
├── refine-config.local.json      ← Configuração local (gitignored)
├── generate-context.sh           ← Gera contexto-implementacao.md
├── generate-index.sh             ← Regenera INDEX.md
├── validate-ticket.sh            ← Valida consistência entre docs + schema JSON
├── completions.sh                ← Auto-complete bash
│
├── lib/
│   ├── utils.sh                  ← Funções compartilhadas de logging
│   ├── jira-fetch.sh             ← Deep fetch Jira
│   ├── code-scan.sh              ← Scan de código multi-linguagem
│   ├── generate-questions.sh     ← Perguntas para o negócio
│   ├── generate-refinement.sh    ← Refinamento técnico
│   ├── generate-tasks.sh         ← Wrapper shell para generate-tasks.py
│   ├── utils.py                  ← Funções Python compartilhadas
│   ├── render_template.py        ← Renderizador Mustache-like {{VAR}}
│   ├── assemble_jira.py          ← Monta dados do Jira
│   ├── extract_project_context.py← Extrai padroes arquiteturais do codigo fonte
│   ├── generate_implementation_plan.py ← Plano de implementação (usa projects-context/)
│   ├── generate_tasks.py         ← Gera status-tasks.json automaticamente
│   ├── generate_per_task_jira_text.py ← Texto Jira por subtarefa
│   ├── jira_agile_parse.py       ← Parse de sprints/pontos
│   ├── jira_attachment_dedup.py  ← Download attachments com dedup MD5
│   └── jira_count_attachments.py ← Contagem de attachments
│
├── projects-context/             ← Contexto permanente extraido do codigo fonte
│   ├── _template.md              ← Modelo para novos projetos
│   └── <projeto>.md              ← Gerado por generate-project-context.sh
│
├── templates/
│   ├── refinamento-tecnico-template.md       ← Template base (melhorado)
│   └── refinamento-tecnico-template.md.bak    ← Backup do template original
│
├── hooks/
│   └── commit-msg                ← Hook para validar mensagens
│
├── tests/
│   ├── test_generate_tasks.py    ← 27 testes
│   ├── test_utils.py             ← 20 testes
│   └── test_extracted.py         ← 5 testes
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

**Contexto permanente do projeto:** Use `projects-context/` para obter
informações arquiteturais sem precisar escanear o código fonte a cada
sessão. Estes arquivos são gerados por `generate-project-context.sh` e
contêm pacotes, anotações, endpoints, classes de referência e convenções.

Para listar projetos com contexto disponível:

```bash
ls projects-context/*.md | grep -v _template
```

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

a) Gerar documentação — Buscar dados do Jira e criar planos + subtarefas
b) Implementar uma task — Executar uma subtarefa específica
c) Verificar status — Mostrar progresso do ticket e subtarefas
```

### Passo 5: Se for gerar documentação, pergunte granularidade

```
Que nível de granularidade você quer para as tasks?

a) Grossa (3 tasks) — recomendado para tickets simples
   Ex: CRUD completo, Lógica de processamento
b) Média (6-7 tasks) — cada camada de desenvolvimento
   Ex: Entity+Repo, DTOs, Service, Controller, Testes
c) Fina (10-11 tasks) — cada classe individualmente
   Ex: Migration, Entity, DTOs, Repo, Mapper, Service, Controller, Testes
```

### Passo 6: Pergunte sobre artefatos de demonstração

Antes de gerar as tasks, pergunte se deseja incluir task de demonstração:

```
Deseja incluir artefatos de demonstração (roteiro-demo.md, Postman, queries SQL)?

a) Sim
b) Não (padrão)
```

**Regras (aplicadas na geração das tasks):**
- Se `b` (padrão): `generate-tasks.sh` gerará tasks **sem** task do tipo `demo`
- Se `a`: `generate-tasks.sh` incluirá uma task `demo` no final da lista
- Tasks `demo` nunca são geradas por padrão — apenas quando o usuário disser "sim"

### Passo 7: Mostre preview e confirme

Após definir granularidade e decisão sobre demo, gere as tasks com `--preview`:

```bash
./lib/generate-tasks.sh tickets/TICKET_ID --granularity media --preview
```

Mostre a tabela gerada para o usuário e pergunte:

```
Tasks para TICKET-123 no modo media (7 tasks):

| ID | Descrição | Nível | Tipo | Depende |
|----|-----------|-------|------|---------|
| ...

Confirma? (s/n)
```

Se `n`, pergunte novamente a granularidade ou permita ajustes manuais.
Se `s`, prossiga.

---

## 5. Geração da Documentação

### 5.1. Leia a documentação do projeto alvo

**REGRRA OBRIGATÓRIA:** Antes de gerar qualquer documento ou subtarefa,
você DEVE ler a documentação do projeto alvo para entender suas
convenções, padrões de código e arquitetura.

**Fonte primária de contexto:** Primeiro verifique se existe um arquivo
em `projects-context/<projeto>.md` (gerado por `generate-project-context.sh`).
Este arquivo contém toda a informação arquitetural extraída do código
fonte — pacotes, anotações, endpoints, classes de referência — e é a
fonte mais rápida e confiável para entender o projeto.

```bash
# Verificar contexto permanente disponivel
ls projects-context/ 2>/dev/null

# Ler contexto do projeto especifico
cat projects-context/<projeto>.md
```

Se `projects-context/<projeto>.md` **não** existir, escaneie o código
fonte manualmente como fallback:

```bash
# 1. Documentação do projeto
ls <caminho-projeto>/README.md
ls <caminho-projeto>/AGENTS.md
ls <caminho-projeto>/docs/        2>/dev/null
ls <caminho-projeto>/*.sdd        2>/dev/null
ls <caminho-projeto>/*.sdd.*      2>/dev/null
ls <caminho-projeto>/SDD*         2>/dev/null
ls <caminho-projeto>/**/sdd*      2>/dev/null

# 2. Estrutura e multi-módulo
ls <caminho-projeto>/settings.gradle
ls <caminho-projeto>/pom.xml
ls <caminho-projeto>/package.json

# 3. Padrões de código do projeto (controllers, services, entities)
ls <caminho-projeto>/src/main/java/**/*Controller.java | head -5
ls <caminho-projeto>/src/main/java/**/*Service.java   | head -5
ls <caminho-projeto>/src/main/java/**/*Entity.java     | head -5
```

Neste caso, considere gerar o contexto permanente para reuso futuro:

```bash
./generate-project-context.sh path/to/projeto
```

Extraia destas fontes:
- **Convenções de nomenclatura**: como controllers, services, entities são nomeados
- **Padrões de pacotes**: estrutura de pacotes (command/controller/service/repository)
- **Padrões de endpoint**: como URLs são definidas (@RequestMapping, @PostMapping, etc.)
- **Tratamento de erros**: como exceptions são lançadas e tratadas
- **DTOs**: padrão de request/response, validações (@NotBlank, @NotNull, etc.)
- **Anotações comuns**: @RequiredArgsConstructor, @Valid, @Slf4j, etc.

Inclua estas descobertas no `observacoes` de cada subtarefa e no
refinamento técnico, para que o dev tenha exemplos concretos do
próprio projeto.

### 5.2. Analise o código fonte

Para cada projeto identificado como afetado:

```bash
# Se projects-context/<projeto>.md existe, ele ja contem toda informacao
# Senao, use os comandos abaixo para escanear manualmente:
```

- Leia `settings.gradle` / `pom.xml` / `package.json` (multi-module?)
- Mapeie pacotes com `ls src/main/java/...` ou `ls src/`
- Identifique padrões de implementação em tickets similares
- Leia uma classe de exemplo de cada tipo (Controller, Service, Entity, DTO)

### 5.3. Gere os arquivos base (agente IA)

> Nota: `implementation-plan.md` agora é gerado pelo pipeline (`--plan`).
> O agente não precisa mais criá-lo manualmente.

1. **`description.md`**: Conteúdo do Jira enriquecido com análise de negócio
2. **`roteiro-demo.md`** *(opcional)*: Script de apresentação para o negócio
3. **`demo-artifacts/`** *(opcional)*: Artefatos da demonstração (Postman, SQL)

> **Artefatos de demonstração NÃO são gerados por padrão.** O agente DEVE
> perguntar ao usuário se deseja criá-los (veja seção 4, Passo 6).
> Só gere `roteiro-demo.md` e `demo-artifacts/` se o usuário disser "sim".

### 5.4. Gere as tasks internas → `status-tasks.json`

> **Nota:** As tasks em `status-tasks.json` são para tracking interno do agente.
> Não são criadas como subtasks no Jira. A especificação completa (incluindo a
> tabela de tasks) vai na descrição do ticket principal via `jira-update-description.sh`.

Cada subtarefa deve ser:
- **Vertical**: agrupa artefatos relacionados (ex: entidade + DTOs + repository em uma task)
- **Executável**: descrição clara do que precisa ser feito
- **Validável**: compila, testa, pode ser verificada
- **Associada a um projeto**: especifica em qual projeto implementar
- **Nível de senioridade**: `nivel` (junior/pleno/senior) para orientar a alocação
- **Baseada na documentação do projeto**: referências a classes/padrões reais

Exemplo de `status-tasks.json` (tracking interno do agente):

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
      "descricao": "Implementar CRUD completo de Funcionalidade",
      "caminhoProjeto": "../projetos/meu-projeto-backend",
      "nivel": "junior",
      "tipo": "implementar",
      "dependeDe": [],
      "bloqueadoPor": null,
      "status": "pendente"
    },
    {
      "id": "0002",
      "projeto": "meu-projeto-backend",
      "descricao": "Implementar logica de processamento/calculo de Funcionalidade",
      "caminhoProjeto": "../projetos/meu-projeto-backend",
      "nivel": "senior",
      "tipo": "alterar-classe",
      "dependeDe": ["0001"],
      "bloqueadoPor": null,
      "status": "pendente"
    }
  ]
}
```

### 5.5. Gere `contexto-implementacao.md`

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

### 6.3. Atualizar descricao no Jira (opcional, mas recomendado)

Após cada task concluída, pergunte ao usuário se deseja sincronizar a descricao do ticket no Jira:

```
Task 0001 concluida. Atualizar descricao no Jira? (s/N)
```

Se sim:

```bash
./lib/jira-update-description.sh TICKET_ID --update-status
```

Isso re-gera o ADF da descrição com os status atualizados e faz PUT no ticket.

### 6.4. Registro no JSON após conclusão

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

### 6.5. Registro no JSON após falha

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
1. Leia a implementação similar de referência (veja seção 5.1)
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

### 9.3. Tipo: `implementar` (servico + endpoint em uma task)

```
1. Leia a documentação do projeto (README, AGENTS.md, SDDs — seção 5.1)
2. Leia uma classe de serviço e um controller existentes como referência
3. Crie a classe de servico com as regras de negocio
4. Crie o controller REST com os endpoints
5. Conecte servico ao controller via injecao de dependencia
6. Siga os padrões de nomenclatura, pacotes e anotações do projeto
7. Compile e teste o fluxo completo
```

### 9.4. Tipo: `testes` (unitarios + integracao consolidados)

```
1. Localize ou crie as classes de teste
2. Use o mesmo framework de mock da base
3. Cubra: sucesso, erro de validacao, bloqueio, fluxo completo
4. Configure ambiente de teste se necessario (WireMock, H2)
```

### 9.5. Tipo: `demo`

**Importante:** Tasks do tipo `demo` só devem ser criadas se o usuário
confirmar explicitamente (veja seção 4, Passo 6). Não gerar tasks `demo`
por padrão — a pergunta deve ser feita **antes** de gerar as tasks.

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

### 9.6. Formato das observacoes

As observacoes de cada task em status-tasks.json devem seguir o formato
de **documentação natural**, sem backticks, sem blocos de codigo, sem steps
numerados e sem tabelas formatadas.

Carregue a skill **doc-natural** para instruções detalhadas e exemplos antes/depois.
O agente DEVE carregar esta skill sempre que for escrever observacoes, description.md
ou refinamento-tecnico.md.

A ferramenta humanize_text.py aplica sanitizacao automatica (remove backticks
e blocos de codigo) antes de enviar ao Jira, mas o ideal e ja escrever no
formato correto para evitar depender de pos-processamento.

---

## 10. Sincronização JSON com MD

O agente SEMPRE:

1. **Lê** `status-tasks.json` primeiro (fonte da verdade)
2. **Executa** a ação
3. **Atualiza** `status-tasks.json` com o novo estado
4. **Sincroniza** `contexto-implementacao.md`
5. **Valida consistência** entre todos os documentos (ver seção 10.1)

```bash
./generate-context.sh TICKET_ID
./validate-ticket.sh TICKET_ID
./generate-index.sh
```

### 10.1. Verificação Obrigatória de Consistência — Pós-Toda-Ação

Após **qualquer** ação (gerar documentação, implementar task, atualizar status), o agente DEVE executar esta verificação de consistência. Ela detecta divergências como "em um lugar tem 7 tasks, em outro tem 16".

#### 10.1.1. Check 1 — Contagem de tasks em `status-tasks.json`

```bash
jq '.tarefas | length' tickets/TICKET_ID/status-tasks.json
```
Esperado: número inteiro positivo. Se for 0 ou null → erro grave.

#### 10.1.2. Check 2 — `contexto-implementacao.md` reflete o mesmo número

```bash
CONTAGEM_JSON=$(jq '.tarefas | length' tickets/TICKET_ID/status-tasks.json)
CONTAGEM_MD=$(grep -c '| *[0-9]\{4\} *|' tickets/TICKET_ID/contexto-implementacao.md 2>/dev/null || echo 0)
if [ "$CONTAGEM_JSON" -ne "$CONTAGEM_MD" ]; then
  echo "ERRO: status-tasks.json tem $CONTAGEM_JSON tasks, contexto-implementacao.md mostra $CONTAGEM_MD"
  echo "Execute: ./generate-context.sh TICKET_ID para sincronizar"
fi
```

#### 10.1.3. Check 3 — Refinamento não referencia dados desatualizados

```bash
REF_FILE="tickets/TICKET_ID/refinamento-tecnico.md"
if [ -f "$REF_FILE" ]; then
  REF_TASKS=$(grep -c '| *[0-9]\{4\} *|' "$REF_FILE" 2>/dev/null || echo 0)
  if [ "$CONTAGEM_JSON" -ne "$REF_TASKS" ]; then
    echo "AVISO: refinamento-tecnico.md tem $REF_TASKS tasks, status-tasks.json tem $CONTAGEM_JSON"
    echo "Regenere o refinamento: ./refine-ticket.sh TICKET_ID --refinement"
  fi
fi
```

#### 10.1.4. Check 4 — Nenhum documento órfão (arquivo sem conteúdo)

```bash
for f in description.md implementation-plan.md roteiro-demo.md jira-summary.md; do
  fpath="tickets/TICKET_ID/$f"
  if [ -f "$fpath" ] && [ ! -s "$fpath" ]; then
    echo "ERRO: $fpath está vazio!"
  fi
done
```

#### 10.1.5. Check 5 — Dependências entre tasks são válidas

```bash
python3 -c "
import json
with open('tickets/TICKET_ID/status-tasks.json') as f:
    data = json.load(f)
task_ids = {t['id'] for t in data['tarefas']}
for t in data['tarefas']:
    for dep in t.get('dependeDe', []):
        if dep not in task_ids:
            print(f'ERRO: task {t[\"id\"]} depende de {dep} que nao existe')
        # tambem verifica se a dependencia nao esta em estado bloqueante final
"
```

#### 10.1.6. Check 6 — Qualidade das observações técnicas

O refinamento deve conter observações técnicas específicas para cada task, especialmente para tasks de nível pleno/senior:

```bash
TASKS_FILE="tickets/TICKET_ID/status-tasks.json"
if command -v jq &>/dev/null; then
  jq -r '.tarefas[] | select(.nivel == "senior" or .nivel == "pleno") | "\(.id): \(.observacoes | length) chars"' "$TASKS_FILE"
  # Observacoes com menos de 100 chars sao consideradas insuficientes
  jq -r '.tarefas[] | select(.nivel == "senior" or .nivel == "pleno") | select((.observacoes // "") | length < 100) | "AVISO: Task \(.id) sem observacoes suficientes"' "$TASKS_FILE"
fi
```

#### 10.1.7. Check 7 — Seções do refinamento técnico

O `refinamento-tecnico.md` deve conter as seguintes seções obrigatórias:

```bash
REF_FILE="tickets/TICKET_ID/refinamento-tecnico.md"
for section in "Dados do Ticket" "Objetivo Funcional" "Impacto Técnico" "Observações Técnicas por Task" "Tasks" "Checklist de Implementação" "Matriz de Rastreabilidade"; do
  if ! grep -qi "$section" "$REF_FILE" 2>/dev/null; then
    echo "ERRO: Seção '$section' não encontrada no refinamento técnico!"
  fi
done
```

As seções **Observações Técnicas por Task** e **Matriz de Rastreabilidade** são obrigatórias para o refinamento — a primeira fornece orientação direta ao desenvolvedor, a segunda vincula perguntas de negócio a decisões técnicas e tasks.

#### 10.1.8. Check 8 — Tasks referenciam projetos válidos

```bash
TASKS_FILE="tickets/TICKET_ID/status-tasks.json"
if [ -d "projects-context" ] && command -v jq &>/dev/null; then
  jq -r '.tarefas[] | "\(.id) → projeto: \(.projeto // "?"), caminho: \(.caminhoProjeto // "?")"' "$TASKS_FILE" | while IFS= read -r line; do
    projeto=$(echo "$line" | sed 's/.*projeto: //;s/, caminho:.*//')
    ctx_file="projects-context/${projeto}.md"
    if [ ! -f "$ctx_file" ]; then
      echo "AVISO: Projeto '$projeto' nao tem arquivo em projects-context/"
    fi
  done
fi
```

#### 10.1.9. Se qualquer check falhar

| Ação | O que fazer |
|------|-------------|
| Check 1 ou 2 falham | Executar: `./generate-context.sh TICKET_ID && ./generate-index.sh` e re-verificar |
| Check 3 falha | Regerar refinamento: `./refine-ticket.sh TICKET_ID --refinement` |
| Check 6 falha | Regerar refinamento com observações técnicas aprimoradas |
| Check 7 falha | Verificar template e regerar refinamento |
| Check 8 falha | Verificar projetos em `refine-config.json` e gerar `projects-context/` |
| Arquivo vazio | Remover ou regenerar o documento específico |
| Dependência inválida | Corrigir `dependeDe` no `status-tasks.json` manualmente |

Após corrigir, repetir os checks até passarem todos antes de prosseguir.

---

## 11. Exemplo de Sessão Completa

```
Usuário: "gere documentacao para PROJ-123"
Agente:
├── Verifica se projects-context/<projeto>.md existe
├── refine-ticket.sh PROJ-123 --refine   ← Pipeline: fetch + scan + perguntas + refinamento
├── Lê jira-data.json e projects-context/<projeto>.md para entender estrutura
├── Pergunta granularidade → usuário escolhe "media"
├── Pergunta se deseja artefatos de demonstração → usuário escolhe "não"
├── Gera tasks sem demo: ./lib/generate-tasks.sh PROJ-123 --granularity media
├── Mostra preview e confirma
├── Gera description.md
├── Implementation-plan.md enriquecido com contexto do projeto
├── Status-tasks.json gerado automaticamente
├── Contexto-implementacao.md gerado e validado
└── "Documentacao criada. 6 tasks em status-tasks.json."

Usuário: "adicione a task 'Criar endpoints de exportacao' no PROJ-123"
Agente:
├── Lê status-tasks.json atual (7 tasks existentes)
├── Pergunta nivel, tipo e dependencias da nova task
├── Adiciona task 0008 no JSON
├── Re-gera implementation-plan.md com blueprint para 8 tasks
├── Re-gera contexto-implementacao.md
├── Valida consistencia
└── "Task 0008 adicionada. Plano atualizado."

Usuário: "implemente a task 0001 do PROJ-123"
Agente:
├── Le status-tasks.json: 0001 pendente
├── Carrega skill doc-natural para formato das observacoes
├── Marca 0001 como em_andamento
├── Instala pre-commit hook
├── Implementa conforme contexto do projeto (entities, servicos, etc.)
├── Compila e testa
├── Squash commits com git commit -m "PROJ-123-0001: descricao"
├── Marca 0001 como concluido
├── Atualiza contexto-implementacao.md
├── "Atualizar descricao no Jira?"
│   ├── sim → jira-update-description.sh PROJ-123 --update-status
│   └── nao → continua
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

- [ ] Verifiquei se `projects-context/<projeto>.md` existe (fonte de contexto mais rapida)
- [ ] Li `projects-context/<projeto>.md` se disponivel
- [ ] Li `settings.gradle`/`pom.xml`/`package.json` dos projetos
- [ ] Mapeei os pacotes de cada módulo
- [ ] Identifiquei corretamente a ordem de dependência entre módulos
- [ ] Li README.md, AGENTS.md e SDDs do projeto alvo
- [ ] Extraí convenções de código (controllers, services, entities, endpoints)
- [ ] As subtarefas cobrem todos os projetos afetados
- [ ] Dependências entre subtarefas estão corretas

---

## 14. Verificação Cruzada de Documentos

- [ ] `status-tasks.json` reflete o estado real
- [ ] `contexto-implementacao.md` reflete o mesmo estado
- [ ] `INDEX.md` reflete progresso atualizado
- [ ] `implementation-plan.md` não referencia arquivos desatualizados
- [ ] `roteiro-demo.md` está alinhado com o estado real
- [ ] `observacoes` das subtarefas contêm exemplos concretos do projeto
- [ ] Nomes de classes/pacotes mencionados existem de fato no código

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
5. **Generate Plan** → `implementation-plan.md` via `generate_implementation_plan.py` (usa `projects-context/` se disponivel)
6. **Validation** → `validate-ticket.sh` verifica schema JSON e consistência entre docs

### 15.3. Configuração

```bash
export JIRA_USER="email@empresa.com"
export JIRA_TOKEN="seu-token"
export JIRA_BASE="https://meujira.atlassian.net"
```

Copie `refine-config.json` → `refine-config.local.json` e ajuste para seu projeto.

### 15.4. Fluxo de Uso

```
TECH LEAD (documentacao completa em 1 comando):
1. ./gerar-documentacao.sh PROJ-123
2. Revisar perguntas-negocio.md e enviar para o PO
3. Copiar refinamento-tecnico.md para o Jira (campo de especificacao)
4. Status-tasks.json gerado automaticamente com observacoes tecnicas
5. Repassar para o time dev ou implementar via agente
```

### 15.5. Documentos Gerados

| Arquivo | Conteúdo | Para quem |
|---------|----------|-----------|
| `jira-data.json` | Dados completos do Jira (épico, links, comentários) | Agente IA |
| `jira-summary.md` | Resumo legível do ticket | Tech lead |
| `impact-report.json` | Estrutura dos projetos de código | Agente IA |
| `perguntas-negocio.md` | Tabela de perguntas para o negócio | PO / Analista |
| `refinamento-tecnico.md` | Documento completo de refinamento com seções de observações técnicas por task e matriz de rastreabilidade | Time dev |
| `status-tasks.json` | Tasks internas (tracking do agente) com observações técnicas, esforço estimado e enriquecimento via `projects-context/` | Agente IA / Dev |
| `implementation-plan.md` | Plano de implementação, arquitetura, cronograma | Time dev |
| `contexto-implementacao.md` | Resumo visual com tabela de subtarefas, gráfico Mermaid de dependências e esforço estimado | Dev |
| `description.md` | Conteúdo do Jira enriquecido com análise de negócio | Agente IA |
| `roteiro-demo.md` | *(opcional)* Script de apresentação para o negócio | PO / Dev |
| `demo-artifacts/` | *(opcional)* Postman collection, environment, queries SQL | Dev |

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

---

## 16. Fluxo Interativo de Geração de Documentação

Quando o usuário pedir "gere documentação para PROJ-123", siga este fluxo:

### Passo 1: Pipeline base

```bash
./refine-ticket.sh PROJ-123 --refine
```

Isso gera `jira-data.json`, `jira-summary.md`, `impact-report.json`, perguntas, refinamento técnico e tasks iniciais (granularidade auto-detectada).

### Passo 2: Verifique a granularidade sugerida

A granularidade agora é auto-detectada baseada na complexidade do ticket:

```bash
./lib/generate-tasks.sh tickets/PROJ-123 --suggest
```

Exemplo de saída:
```
Granularidade sugerida: media
Motivo: Pontuacao 7/10: complexidade media, 6-7 tasks recomendadas
```

Caso queira alterar manualmente, pergunte ao usuário:

```
Granularidade auto-detectada: media (6-7 tasks). Deseja alterar?

a) Grossa (3 tasks) — recomendado para tickets simples
   Ex: CRUD completo, Lógica de processamento

b) Média (6-7 tasks) — cada camada de desenvolvimento
   Ex: Migration+Entity, DTOs, Service, Controller, Testes

c) Fina (10-11 tasks) — cada classe individualmente
   Ex: Migration, Entity, DTOs, Repository, Mapper, Service, Controller, Testes
```

### Passo 3: Pergunte sobre artefatos de demonstração

Antes de gerar as tasks, pergunte se deseja incluir task de demonstração:

```
Deseja incluir artefatos de demonstração (roteiro-demo.md, Postman, queries SQL)?

a) Sim
b) Não (padrão)
```

**Regras (aplicadas na geração das tasks):**
- Se `b` (padrão): `generate-tasks.sh` gerará tasks **sem** task do tipo `demo`
- Se `a`: `generate-tasks.sh` incluirá uma task `demo` no final da lista
- Tasks `demo` nunca são geradas por padrão — apenas quando o usuário disser "sim"

### Passo 4: Preview Interativo

Use `--interactive` para preview com ajuste de tasks:

```bash
./lib/generate-tasks.sh tickets/PROJ-123 --interactive
```

O modo interativo mostra as tasks uma a uma e permite:
- Alterar granularidade
- Detalhar uma task específica (observações, esforço)
- Confirmar ou cancelar

Ou use `--preview` apenas para visualizar:

```bash
./lib/generate-tasks.sh tickets/PROJ-123 --granularity media --preview
```

Mostre a tabela gerada e pergunte confirmação:

```
Tasks para PROJ-123 no modo media (7 tasks):

| ID | Descrição | Nível | Tipo | Depende |
|----|-----------|-------|------|---------|
| 0001 | Criar entidade + migration + repository | junior | criar-classe | - |
| 0002 | Criar DTOs + mapper | junior | criar-classe | 0001 |
| ... | ... | ... | ... | ... |

Confirma? (s/n)
```

Se `n`, pergunte novamente a granularidade ou permita ajustes manuais.
Se `s`, prossiga.

### Passo 5: Geração completa

```bash
# Re-gerar tasks com a granularidade escolhida
./lib/generate-tasks.sh tickets/PROJ-123 --granularity media

# Gerar plano de implementaçao detalhado
python3 lib/generate_implementation_plan.py tickets/PROJ-123

# Atualizar contexto visual e validaçao
./generate-context.sh PROJ-123
./validate-ticket.sh PROJ-123
./generate-index.sh
```

### Passo 6: Documentos gerados

Informe ao usuário os documentos criados e onde encontrá-los.

---

## 17. Adicionar Task em Ticket Existente

Quando o usuário pedir "adicione a task X ao ticket PROJ-123":

### Passo 1: Leia o estado atual

```bash
# Ler tasks existentes
cat tickets/PROJ-123/status-tasks.json | jq '.tarefas | length'
```

### Passo 2: Pergunte os detalhes da nova task

```
Detalhes da nova task:
- Descrição: (ex: "Criar endpoints de exportação")
- Nível: (junior / pleno / senior)
- Tipo: (implementar / criar-classe / alterar-classe / testes / demo)
- Depende de quais tasks? (ex: 0001, 0003)
```

### Passo 3: Adicione no JSON

Calcule o próximo ID sequencial e insira:

```bash
# Exemplo: adicionar task 0008
NEXT_ID=$(jq '[.tarefas[].id | tonumber] | max + 1 | tostring | "0000"[:4 - length] + .' tickets/PROJ-123/status-tasks.json)
jq --arg id "0008" \
   --arg desc "Criar endpoints de exportacao" \
   --arg nivel "junior" \
   --arg tipo "adicionar-endpoint" \
   --arg deps '["0001"]' \
   '.tarefas += [{
     "id": $id,
     "projeto": .tarefas[0].projeto,
     "descricao": $desc,
     "caminhoProjeto": .tarefas[0].caminhoProjeto,
     "nivel": $nivel,
     "tipo": $tipo,
     "dependeDe": $deps | fromjson,
     "bloqueadoPor": null,
     "status": "pendente"
   }]' tickets/PROJ-123/status-tasks.json > tmp.json && mv tmp.json tickets/PROJ-123/status-tasks.json
```

### Passo 4: Re-gerar documentos

```bash
# Re-gerar plano de implementaçao incluindo a nova task
python3 lib/generate_implementation_plan.py tickets/PROJ-123

# Re-gerar contexto visual
./generate-context.sh PROJ-123

# Validar consistencia
./validate-ticket.sh PROJ-123

# Atualizar indice
./generate-index.sh
```

### Passo 5: Confirme ao usuário

```
Task 0008 adicionada ao PROJ-123.
Plano de implementaçao atualizado com 8 tasks.
Consistencia validada.
```

---

## 18. Atualizar Descrição no Jira

Após gerar a documentação de um ticket, o agente DEVE perguntar ao usuário se deseja atualizar a descrição do ticket principal no Jira com a especificação completa + breakdown de tasks.

> **Nota:** Não são criadas subtasks no Jira. O breakdown de tasks fica na descrição do ticket principal, em formato de tabela com status.

### Fluxo

```
Voce: "Documentacao gerada. Deseja atualizar a descricao do ticket no Jira agora?"
Usuario: sim
Agente: bash lib/jira-update-description.sh TICKET_ID
```

O script `lib/jira-update-description.sh` faz todo o trabalho:
1. Lê `description.md`, `status-tasks.json` e `refinamento-tecnico.md`
2. Monta descrição markdown completa: objetivo + tasks + observações + riscos
3. Converte para ADF (Atlassian Document Format)
4. Faz PUT na descrição do ticket via REST API

### Preview sem enviar

```bash
bash lib/jira-update-description.sh TICKET_ID --dry-run
```

Mostra o markdown completo e métricas (tamanho, tasks) sem chamar a API.

### Atualizar status após task concluída

```bash
bash lib/jira-update-description.sh TICKET_ID --update-status
```

Re-gera a descrição com os status atualizados das tasks.

### Integração no Pipeline

O `gerar-documentacao.sh` já pergunta automaticamente ao final:
```
Deseja atualizar a descricao do ticket TICKET_ID no Jira agora? (s/N)
```

### Conteúdo da Descrição no Jira

A descrição atualizada contém:
- **Objetivo funcional** (do `description.md`)
- **Critérios de aceitação**
- **Tabela de tasks** com ID e descrição
- **Observações técnicas por task** (da `observacoes` em `status-tasks.json`)
- **Riscos técnicos** e **decisões pendentes** (do `refinamento-tecnico.md`)
- **Matriz de rastreabilidade**

### Verificação

```bash
# Verificar ultima atualizacao
jq -r '.ultimaAtualizacao' tickets/TICKET_ID/status-tasks.json
```

---

## 19. Code Review de Pull Requests

Quando um dev abrir um PR no Bitbucket e você quiser revisar:

```
Você: "review PR 123"
```

### Fluxo

1. **Agente descobre o projeto** do ticket ativo (lê `caminhoProjeto` em `status-tasks.json`)
2. **Busca arquivos e diff** via `lib/code-review.sh`:
   ```bash
   bash lib/code-review.sh <projeto> <PR> files   # lista arquivos alterados
   bash lib/code-review.sh <projeto> <PR> diff    # diff completo
   ```
   Exemplo:
   ```bash
   bash lib/code-review.sh dataa-tesouraria 123 files
   bash lib/code-review.sh dataa-tesouraria 123 diff
   ```
3. **Agente analisa** o diff contra as convenções do projeto em `projects-context/<projeto>.md`:
   - Nomenclatura de classes/pacotes segue o padrão existente?
   - Anotações usadas (`@RequiredArgsConstructor`, `@Valid`, `@Resource`) seguem o padrão?
   - Endpoints seguem o padrão REST do projeto?
   - Pacotes corretos (cada classe no lugar certo)?
   - Tratamento de erros (exceptions, `ResponseEntity`)?
   - Testes de integração inclusos?

4. **Varredura cruzada com `diffscan`** (obrigatório):

   Após identificar um padrão com problema no passo 3, o agente DEVE escanear **todos os arquivos do diff** em busca do mesmo padrão antes de apresentar o relatório:

   ```bash
   bash lib/code-review.sh <projeto> <PR> diffscan "<regex>"
   ```

   Exemplo:
   ```bash
   bash lib/code-review.sh dataa-tesouraria 860 diffscan "replace\(n\.textoNumeracao"
   ```

   Isso retorna JSON com todos os arquivos e linhas onde o padrão aparece, permitindo que o agente veja de uma vez se o problema se repete em múltiplos arquivos.

   **Regras:**
   - Se o mesmo problema aparecer em N arquivos, incluir **todos** no relatório
   - Só postar depois de ter analisado todos os arquivos afetados

5. **Agente apresenta relatório consolidado** com sugestões por linha:

   ```
   ## Review do PR #123 — SPR-3420
   Projeto: dataa-tesouraria

   📁 ParametroRecursoGarantidorController.java:15
   ⚠️ Usar @RequiredArgsConstructor em vez de @Resource
   Padrão do projeto: FechamentoContabilController.java usa @Resource

   📁 ParametroRecursoGarantidorService.java:42
   ⚠️ Adicionar @Valid no parâmetro do método calcular()

   ✅ Estrutura de pacotes OK
   ✅ Nomenclatura segue padrão do projeto

   Total: 2 sugestões, 2 ok
   ```

6. **Pergunta**:
   ```
   Deseja postar os comentários no PR?
   a) Postar todos os comentários
   b) Postar apenas os selecionados
   c) Não postar, apenas exibir
   ```

7. **Se "a" ou "b"**, agente constrói o JSON com **TODOS** os comentários em lote único e posta de uma vez:
   ```bash
   bash lib/code-review.sh <projeto> <PR> post /tmp/comments.json
   ```

   **Regra obrigatória:** NUNCA postar comentários separadamente. Todo o lote de comentários deve ser construído e postado em uma única chamada `post`. Se o usuário aprovar e depois pedir um novo comentário, este deve ser um novo lote separado — mas a análise inicial deve cobrir todos os arquivos de uma vez.

8. **Finalizar revisão** — o usuário pode encerrar a revisão de um PR a qualquer momento com `finalizei` / `PR finalizado` / `done` / `encerrei`. O agente DEVE:
   - Descartar todos os comentários pendentes não postados
   - Limpar o contexto de PR ativo (projeto, número, diff)
   - Registrar mentalmente que o PR foi finalizado
   - Ficar pronto para receber um novo PR sem risco de postar no anterior

   ```bash
   # Exemplo:
   Você: "finalizei o PR 763, analise o PR 864"

   Agente:
   ├── PR #763 finalizado — comentarios pendentes descartados
   ├── Busca diff do PR #864
   └── ...
   ```

### Formato do JSON de comentários

Cada comentário inline segue o formato da API do Bitbucket Cloud:

```json
[
  {
    "content": {"raw": "Usar @RequiredArgsConstructor em vez de @Resource"},
    "inline": {"to": 15, "path": "ParametroRecursoGarantidorController.java"}
  },
  {
    "content": {"raw": "Adicionar @Valid no parâmetro do método"},
    "inline": {"to": 42, "path": "ParametroRecursoGarantidorService.java"}
  }
]
```

- `to`: número da linha no arquivo (versão nova)
- `path`: caminho do arquivo dentro do repositório
- `content.raw`: texto do comentário (markdown)

### Credenciais

O script suporta três formas de autenticação no Bitbucket (nesta ordem):

| Fonte | Exemplo |
|-------|---------|
| `~/.bitbucket-credentials` | `email:token_bitbucket` |
| `~/.jira-credentials` (fallback) | `email:token_jira` |
| Env vars | `JIRA_USER` + `BITBUCKET_APP_PASSWORD` |

> **Nota:** App Passwords foram deprecados e serão removidos em Julho de 2026. Use **Atlassian API tokens** com escopos específicos para cada aplicativo:
> - Token Jira (escopo Jira) → `~/.jira-credentials`
> - Token Bitbucket (escopo Pull requests Read/Write) → `~/.bitbucket-credentials`

Para criar um token: https://id.atlassian.com/manage/api-tokens  
Permissão necessária: **Pull requests (Read + Write)**

### Lista de verificação para o agente

Ao revisar um PR, o agente DEVE verificar:

- [ ] Nomes de classes/pacotes seguem o padrão do projeto
- [ ] Anotações seguem o padrão existente (projetos-context)
- [ ] Endpoints REST usam `@RequestMapping`, `@GetMapping`, `@PostMapping` conforme padrão
- [ ] Métodos usam `@Valid` e `@RequestBody` nos parâmetros
- [ ] Tratamento de erros com `ResponseEntity`
- [ ] Injeção de dependência com `@RequiredArgsConstructor` ou `@Resource` (conforme padrão)
- [ ] Testes de integração inclusos
- [ ] Código não referencia SDD, levels (junior/senior/pleno), ou artefatos de demo

---

## 20. Documentação OpenAPI / API-First

### 20.1. Quando gerar

A especificação OpenAPI é gerada automaticamente pelo pipeline sempre que o ticket envolver endpoints de API. A detecção é automática via `generate_openapi_spec.py`:

- **Keywords** que disparam a geração: endpoint, api, controller, rest, @PostMapping, @GetMapping, etc.
- **Tasks do tipo** `adicionar-endpoint` sempre disparam
- **Observações** com code blocks contendo `@RequestMapping`, `@RequestBody`, `ResponseEntity`

### 20.2. Pipeline

```
gerar-documentacao.sh: step 6.5 → generate_openapi_spec.py → openapi.yaml
jira-update-description.sh: parse openapi.yaml → markdown tables → ADF description + attachment
```

### 20.3. Arquivos gerados

| Arquivo | Conteúdo | Onde fica |
|---------|----------|-----------|
| `openapi.yaml` | Especificação OpenAPI 3.0 completa | `tickets/TICKET_ID/openapi.yaml` |
| Tabelas na descrição do Jira | Endpoints (método + path + descrição) + Schemas (campos + tipos) | Descrição do ticket no Jira |
| Attachment no Jira | `openapi.yaml` anexado ao ticket para download | Ticket no Jira |

### 20.4. Fontes de dados para a OpenAPI

O `generate_openapi_spec.py` extrai informações de múltiplas fontes:

1. **`description.md`** — tabelas de endpoints e schemas, exemplos JSON
2. **`status-tasks.json`** — observações com code blocks Java contendo `@PostMapping`, `@RequestBody`, classes DTO
3. **`projects-context/<projeto>.md`** — `@RequestMapping` base paths, `@Tag(name = "...")`
4. **Código fonte do projeto** — DTOs reais do diretório `src/main/java/` (Input, Output, DTO, Filter, Request, Response)
5. **`refine-config.json` / `refine-config.local.json`** — `apiBaseUrl` do projeto

### 20.5. Estrutura do openapi.yaml

```yaml
openapi: "3.0.3"
info:
  title: "SPR-3459: Resumo do ticket"
  version: "2026-01-01"
servers:
  - url: https://api.exemplo.com
    description: Ambiente de produção
tags:
  - name: "Conta Contabil"
    description: "Endpoint de conta contabil"
paths:
  /api/contas/buscar:
    get:
      operationId: "get_api_contas_buscar"
      summary: "Buscar conta contabil"
      parameters:
        - name: filtro
          in: query
          required: true
          schema:
            type: string
      responses:
        "200":
          description: "Operação realizada com sucesso"
components:
  schemas:
    ContaContabilBuscarResponse:
      type: object
      properties:
        id:
          type: integer
        numeracao:
          type: string
        nome:
          type: string
```

### 20.6. Templates

O template OpenAPI usa a sintaxe Mustache-like do `render_template.py`:

| Sintaxe | Uso |
|---------|-----|
| `{{VAR}}` | Substituição de variável |
| `{% if VAR %}`...`{% endif %}` | Condicional |
| `{% for item in LIST %}`...`{% endfor %}` | Iteração |

Variáveis disponíveis no template:

| Variável | Fonte | Exemplo |
|----------|-------|---------|
| `{{TICKET_ID}}` | Nome do diretório do ticket | `SPR-3459` |
| `{{SUMMARY}}` | `jira-data.json → summary` | `Criar busca de conta contabil` |
| `{{DATE}}` | Data atual | `2026-01-01` |
| `{{SERVERS}}` | `refine-config.json → apiBaseUrl` | `https://api.exemplo.com` |
| `{{API_TAGS}}` | `projects-context/` tags | Lista de `{name, description}` |
| `{{ENDPOINTS}}` | Extraído de tasks + desc | Lista de endpoints |
| `{{SCHEMAS}}` | Extraído de tasks + DTOs fonte | Dict de schemas |
| `{{PROJECT_NAME}}` | `refine-config.json` | `dataa-tesouraria` |

### 20.7. Customização de apiBaseUrl

Para que a OpenAPI inclua a URL base do servidor, configure `apiBaseUrl` no projeto em `refine-config.local.json`:

```json
{
  "projects": [
    {
      "name": "meu-projeto",
      "apiBaseUrl": "https://api.exemplo.com"
    }
  ]
}
```

Se `apiBaseUrl` estiver vazio ou ausente, a seção `servers` será omitida do YAML.

### 20.8. Atualização após implementação

Quando tasks são concluídas e novos endpoints são implementados:

```bash
python3 lib/generate_openapi_spec.py tickets/TICKET_ID
```

Isso re-gera o `openapi.yaml` com novos endpoints e schemas detectados das observações atualizadas. Em seguida, re-envie ao Jira:

```bash
bash lib/jira-update-description.sh TICKET_ID --update-status
```

O script atualizará as tabelas na descrição e fará upload do novo YAML como attachment (substituindo o anterior no Jira).

---

## 21. Humanização Automática de Texto

O pipeline aplica humanização automática no texto enviado ao Jira e ao
Bitbucket, removendo marcadores visíveis de template (`---`, `***`, `___`)
e colapsando linhas em branco múltiplas.

### 21.1. Onde é aplicada

| Ponto | Modo | Transformações |
|-------|------|----------------|
| `jira-update-description.sh` | `--jira` | Remove `---`, `***`, `___`; colapsa blanks; preserva `#` (necessário para ADF) |
| `code-review.sh post` | `--pr` | Converte `#` → `**texto**`; remove separadores; colapsa blanks; converte tabelas 2-3 colunas para listas |

### 21.2. Comportamento padrão

- **Jira:** humanização ON (não configurável)
- **Bitbucket PR:** humanização ON por padrão. Use `--no-humanize` para desligar:

```bash
bash lib/code-review.sh projeto 123 post /tmp/comments.json --no-humanize
```

### 21.3. Engine

`lib/humanize_text.py` lê markdown via stdin, escreve texto humanizado via stdout.

```bash
cat input.md | python3 lib/humanize_text.py --jira
cat input.md | python3 lib/humanize_text.py --pr
```

### 21.4. Regras para o agente

- PR comments devem ser escritos em linguagem natural, sem `##`, `---`, ou tabelas
- O agente não precisa se preocupar com a formatação técnica — o `humanize_text.py` lida com isso
- Para dry-run do Jira, o preview mostra o markdown já humanizado (o que de fato será enviado)
