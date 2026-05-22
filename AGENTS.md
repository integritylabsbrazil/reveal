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
   Ex: CRUD, Lógica, Demo
b) Média (6-7 tasks) — cada camada de desenvolvimento
   Ex: Entity+Repo, DTOs, Service, Controller, Testes, Demo
c) Fina (10-11 tasks) — cada classe individualmente
   Ex: Migration, Entity, DTOs, Repo, Mapper, Service, Controller, Testes, Demo
```

### Passo 6: Mostre preview e confirme

Após escolher a granularidade, gere as tasks com `--preview`:

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
Se `s`, prossiga com a geração completa.

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
2. **`roteiro-demo.md`**: Script de apresentação para o negócio
3. **`demo-artifacts/`**: Artefatos da demonstração (Postman, SQL)

### 5.4. Gere as subtarefas → `status-tasks.json`

Cada subtarefa deve ser:
- **Vertical**: agrupa artefatos relacionados (ex: entidade + DTOs + repository em uma task)
- **Executável**: descrição clara do que precisa ser feito
- **Validável**: compila, testa, pode ser verificada
- **Associada a um projeto**: especifica em qual projeto implementar
- **Nível de senioridade**: `nivel` (junior/pleno/senior) para orientar a alocação
- **Baseada na documentação do projeto**: referências a classes/padrões reais

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
    },
    {
      "id": "0003",
      "projeto": "meu-projeto-backend",
      "descricao": "Preparar artefatos de demonstracao de Funcionalidade",
      "caminhoProjeto": "../projetos/meu-projeto-backend",
      "nivel": "junior",
      "tipo": "demo",
      "dependeDe": ["0001"],
      "bloqueadoPor": null,
      "status": "pendente",
      "esforcoEstimado": {"horas": 4, "descricao": "medio (~4h)"},
      "artefatos": ["roteiro-demo.md", "postman-collection.json", "postman-environment.json", "queries.sql"]
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

### 9.6. Formato das `observacoes` (markdown livre → ADF no Jira)

O campo `observacoes` de cada task em `status-tasks.json` é escrito em **markdown puro**.
O `build_adf.py` converte para ADF (Atlassian Document Format) automaticamente,
reconhecendo os seguintes elementos:

| Markdown | Renderização no Jira |
|----------|---------------------|
| `# Titulo` | Heading (seção) |
| `## Subtitulo` | Sub-heading |
| ` ```java ... ``` ` | Code block com syntax highlight (```java, ```xml, ```yaml) |
| `\| cel \| cel \|` (2+ linhas) | Tabela |
| texto livre | Parágrafo |

**Regras obrigatórias:**

1. Use `#` para seções, não texto maiúsculo (`# Objetivo`, `# Arquivos Afetados`, etc.)
2. Code blocks DEVEM ter o language identifier: ` ```java`, ` ```xml`, ` ```yaml`, ` ```json`
3. Tabelas: primeira linha é o header, segunda linha separadora `|---|---|`, demais linhas dados
4. Classe **nova**: escrever `NOVA: NomeSugeridoCamelCase.java` na descrição
5. Classe **alterada**: mencionar o path real e o que muda
6. **JSON de resposta:** incluir `# Exemplo de Resposta` com ` ```json` contendo request/response real extraído do DTO do projeto — não inventar campos

**Exemplo de `observacoes`:**

```markdown
# Objetivo
Possibilitar busca de conta contabil por numeracao sem pontuacao.

# Arquivos Afetados
| Arquivo | Acao | Pacote |
|---------|------|--------|
| ContaContabilRepositoryCustomImpl.java | ALTERAR | com.maps.dataa.tesouraria.contaContabil.repository |
| NormalizacaoUtils.java | NOVA | com.maps.dataa.tesouraria.common |

# Implementacao
1. Criar `NormalizacaoUtils` com metodo estatico
   ```java
   public static String normalizarFiltro(String filtro) {
       return filtro.replaceAll("[-.\\/]", "");
   }
   ```
2. Alterar query JPQL para usar REPLACE

# Codigo de Exemplo
```java
// FavorecidoGetAction.java:53 — normalizacao existente
filtro.replaceAll("-","").replaceAll("\\.","").replaceAll("/","")
```

# Exemplo de Resposta

GET /api/tesouraria/conta-contabil/autocomplete?filtro=101

```json
[
  {
    "id": 1,
    "numeracao": "1.01.01.00.00.00.00.00",
    "nome": "ATIVO CIRCULANTE - CAIXA",
    "idPlanificacao": 5,
    "planificacaoAtiva": true
  }
]
```

# Criterios de Aceitacao
| Cenario | Resultado Esperado |
|---------|-------------------|
| Busca "101" sem pontuacao | Encontra "1.01.00.00.00.00.00" |
| Busca "1.01" com pontuacao | Encontra mesma conta (compatibilidade) |
```

> O agente DEVE extrair os exemplos de código do `projects-context/<projeto>.md`
> e do próprio código fonte, garantindo que sejam REAIS e ESPECÍFICOS da task,
> não skeletons genéricos. Classes de referência que não têm relação com a task
> NÃO devem ser incluídas.

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
├── Mostra preview: ./generate-tasks.sh PROJ-123 --granularity media --preview
├── Confirma? → sim
├── Re-gera tasks com granularidade escolhida
├── Gera description.md, roteiro-demo.md
├── Cria demo-artifacts/ (postman-collection, environment, queries)
├── Implementation-plan.md enriquecido com contexto do projeto
├── Status-tasks.json gerado automaticamente
├── Contexto-implementacao.md gerado e validado
└── "Documentacao criada. 7 tasks em status-tasks.json."

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
├── Lê status-tasks.json: 0001 pendente
├── Lê implementation-plan.md para guia por task com blueprint
├── Marca 0001 como "em_andamento"
├── Instala pre-commit hook
├── Implementa exatamente conforme blueprint (entity, DTOs, repository...)
├── Compila e testa
├── Squash commits → git commit -m "PROJ-123-0001: Criar entidade + migration"
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
| `status-tasks.json` | Subtarefas atômicas com observações técnicas, esforço estimado e enriquecimento via `projects-context/` | Agente IA / Dev |
| `implementation-plan.md` | Plano de implementação, arquitetura, cronograma | Time dev |
| `contexto-implementacao.md` | Resumo visual com tabela de subtarefas, gráfico Mermaid de dependências e esforço estimado | Dev |
| `description.md` | Conteúdo do Jira enriquecido com análise de negócio | Agente IA |
| `roteiro-demo.md` | Script de apresentação para o negócio | PO / Dev |
| `demo-artifacts/` | Postman collection, environment, queries SQL | Dev |

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
   Ex: CRUD completo, Lógica de processamento, Demo

b) Média (6-7 tasks) — cada camada de desenvolvimento
   Ex: Migration+Entity, DTOs, Service, Controller, Testes, Demo

c) Fina (10-11 tasks) — cada classe individualmente
   Ex: Migration, Entity, DTOs, Repository, Mapper, Service, Controller, Testes, Demo
```

### Passo 3: Preview Interativo

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

### Passo 4: Geração completa

Se a granularidade escolhida for diferente de `grossa`:

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

### Passo 5: Documentos gerados

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

## 18. Criar Subtasks no Jira

Após gerar a documentação de um ticket, o agente DEVE perguntar ao usuário se deseja criar as subtasks no Jira.

### Fluxo

```
Voce: "Documentacao gerada. Deseja criar as subtarefas no Jira agora?"
Usuario: sim
Agente: bash lib/jira-create-tasks.sh TICKET_ID
```

O script `lib/jira-create-tasks.sh` faz todo o trabalho interativo:
1. Lê `status-tasks.json` e identifica tasks sem `jiraKey`
2. Para cada task, mostra preview (descrição, nível, esforço, observações)
3. Pergunta: "Criar subtask no Jira? (s/N/q-sair)"
4. Se `s`: cria via API REST e salva `jiraKey` no JSON
5. Se `N`: pula a task
6. Se `q`: interrompe o processo

### Modo automático

```bash
bash lib/jira-create-tasks.sh TICKET_ID --auto
```

Cria todas as subtasks sem confirmar individualmente.

### Integração no Pipeline

O `gerar-documentacao.sh` já pergunta automaticamente ao final:
```
Deseja criar subtasks no Jira agora? (s/N)
```

### Formato da Subtask no Jira

Cada task vira uma subtask com:
- **Summary:** `TICKET_ID-NNNN: descrição da task`
- **Parent:** ticket pai (ex: SPR-3413)
- **Description:** contém projeto, nível, tipo, esforço e observações técnicas
- **Issue Type:** Sub-task

Após a criação, o campo `jiraKey` é adicionado à task no `status-tasks.json`:
```json
{
  "id": "0001",
  "jiraKey": "SPR-3472",
  "descricao": "..."
}
```

### Verificação

```bash
# Listar tasks com jiraKey
jq '.tarefas[] | {id, jiraKey, status}' tickets/TICKET_ID/status-tasks.json
