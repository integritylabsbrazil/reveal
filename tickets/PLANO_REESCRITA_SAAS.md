# Plano de Reescrita — dataa-tesouraria → SaaS Multi-tenant

## Estratégia Completa de Reescrever o Sistema como um SaaS Moderno para Fundos de Pensão

---

## 1. Filosofia da Reescrita

### 1.1. Por que reescrever, não refatorar?

O sistema atual tem 2.767 classes Java, 30+ domínios, 65 controllers, 80+ actions e **0,05% de cobertura de testes**. Refatorar um monolito deste porte seria mais lento e arriscado do que reescrever com uma arquitetura limpa, por três motivos:

1. **Dívida técnica impede evolução** — 3 padrões de injeção diferentes, pacotes action/actions misturados, acoplamento bidirecional entre contabilidade e favorecido. Cada melhoria exige semanas de engenharia reversa.
2. **Modelo de dados não suporta multi-tenancy** — o esquema atual foi projetado para uma única EFPC. Adicionar tenantId em 200+ tabelas seria uma cirurgia de alto risco.
3. **Testes insuficientes** — 36 classes de teste para 2.767 classes significam que qualquer refatoração é "no escuro". Reescrever com TDD desde o início é mais seguro.

### 1.2. Estratégia: Strangler Fig + Greenfield

Não vamos desligar o sistema atual de uma vez. Vamos **estrangulá-lo** progressivamente:

```
Fase 1 (Meses 1-6):   ┌──────────────┐    ┌──────────────┐
  Conviver em paralelo │  Sistema     │    │  SaaS (novo) │
                       │  Legado      │    │  cadastro    │
                       │  (intocado)  │    │  + lanc.     │
                       └──────┬───────┘    └──────┬───────┘
                              │                   │
                              ▼                   ▼
                       ┌──────────────────────────────────┐
                       │  Banco Compartilhado (leitura)   │
                       │  Legado alimenta SaaS via        │
                       │  eventos de domínio              │
                       └──────────────────────────────────┘

Fase 2 (Meses 7-12):  ┌──────────────┐    ┌──────────────────────────┐
  Domínios migrados   │  Legado      │    │  SaaS completo           │
  um a um             │  contab.     │    │  cadastro + lanc.        │
                       │  (último a   │    │  + conciliação +         │
                       │  sair)       │    │  remessa + contab.       │
                       └──────────────┘    └──────────────────────────┘

Fase 3 (Mês 13+):     ┌──────────────────────────────────────────┐
  SaaS completo        │  SaaS + Strangler removido               │
                       │  Legado desligado                        │
                       └──────────────────────────────────────────┘
```

### 1.3. Premissas da Reescrita

| Premissa | Decisão |
|----------|---------|
| **Multi-tenancy** | Database-per-tenant (isolamento máximo) + schema compartilhado para dados de referência |
| **Primeiro cliente** | A EFPC atual (dataa) será o tenant piloto |
| **Dados históricos** | Migrados apenas 3 anos para trás; saldos abertos são transportados |
| **Paralelismo** | 6 meses de operação paralela obrigatórios |
| **Equipe** | Time dedicado de reescrita + time de sustain do legado |
| **Regras de negócio** | Não copiadas — reimplementadas entendendo o porquê, não o como |

---

## 2. Arquitetura SaaS Multi-tenant

### 2.1. Modelo de Isolamento de Dados

```
                     ┌─────────────────────────────┐
                     │   API Gateway / BFF         │
                     │   (autenticação + tenant    │
                     │    resolution por domínio)  │
                     └──────────┬──────────────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Microserviço A  │  │  Microserviço B  │  │  Microserviço C  │
│  (dados por      │  │  (dados por      │  │  (dados por      │
│   tenant)        │  │   tenant)        │  │   tenant)        │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         │                     │                     │
         ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  DB Tenant 1     │  │  DB Tenant 1     │  │  DB Tenant 1     │
│  DB Tenant 2     │  │  DB Tenant 2     │  │  DB Tenant 2     │
│  DB Tenant N     │  │  DB Tenant N     │  │  DB Tenant N     │
└──────────────────┘  └──────────────────┘  └──────────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                     ┌─────────▼─────────┐
                     │  Shared Registry  │
                     │  (planos de       │
                     │   assinatura,     │
                     │   billing,        │
                     │   feature flags)  │
                     └───────────────────┘
```

**Estratégia de banco de dados:**

| Abordagem | Quando usar |
|-----------|-------------|
| **Database-per-tenant** | Dados transacionais dos fundos (lançamentos, remessas, contabilidade). Isolamento máximo, backup/restore individual. |
| **Schema-per-tenant** | Dados de catálogo compartilhável (planos de contas, naturezas financeiras) que cada tenant pode customizar. |
| **Shared table (com tenantId)** | Dados de referência global (bancos, feriados, tabelas fiscais) — imutáveis e compartilhados entre todos. |

### 2.2. Tecnologia Sugerida

| Componente | Tecnologia | Motivo |
|-----------|-----------|--------|
| **Linguagem** | Java 21+ (Spring Boot 3) ou Kotlin | Domínio complexo, tipagem forte, ecossistema maduro |
| **API** | REST + GraphQL (consultas complexas) | REST para comandos, GraphQL para relatórios/dashboards |
| **Eventos** | Kafka / RabbitMQ | Eventos de domínio entre serviços |
| **Banco transacional** | PostgreSQL (database-per-tenant) | Maturidade, extensibilidade, JSONB para dados semi-estruturados |
| **Banco de relatórios** | ClickHouse | Consultas OLAP sobre grandes volumes de lançamentos |
| **Cache** | Redis | Sessão, cache de consultas frequentes (planos de contas) |
| **Armazenamento** | S3 / MinIO | Documentos anexados, arquivos de remessa, comprovantes |
| **Orquestração** | Kubernetes | Escalabilidade, isolamento de tenants pesados |
| **CI/CD** | GitLab CI / GitHub Actions | Pipeline de build + teste + deploy por tenant piloto |
| **Idempotency** | Idempotency Key (cabeçalho HTTP) | Garantia de entrega de remessas financeiras |

### 2.3. Padrões Arquiteturais

| Padrão | Aplicação |
|--------|-----------|
| **CQRS** | Commands síncronos (criar lançamento) vs. Queries assíncronas (relatório de fechamento) |
| **Event Sourcing** | Lancamentos financeiros (append-only, auditoria nativa) |
| **Saga Coreográfica** | Fechamento contábil multi-etapas (lançamentos → rateio → fechamento → consolidação) |
| **Outbox Pattern** | Garantia de entrega de eventos sem 2PC |
| **BFF (Backend for Frontend)** | Uma API para o portal web, outra para o portal do participante, outra para integração |
| **Feature Flags** | Liberação incremental de módulos por tenant (Unleash / LaunchDarkly) |

---

## 3. Módulos do Novo Sistema

Cada módulo abaixo é um microsserviço independente, com seu próprio banco de dados (database-per-tenant), API REST e eventos de domínio públicos.

### 3.1. Core Domain — Cadastro e Configuração

#### tenant-registry (Serviço de Plataforma)

**Responsabilidade:** Gerenciamento de tenants, planos de assinatura, feature flags, onboarding.

| Comportamento | Descrição |
|--------------|-----------|
| Provisionamento de tenant | Cria database, executa migrations, configura admin inicial |
| Feature flags | Habilita/desabilita módulos por tenant (ex: "conciliação ativa") |
| Métricas de uso | Armazena consumo (participantes ativos, volume de lançamentos) para billing |

**Eventos que publica:**
- `TenantProvisioned` — novo cliente onboarded
- `TenantPlanChanged` — upgrade/downgrade de plano
- `TenantSuspended` — inadimplência

#### cadastro-favorecido

**Responsabilidade:** Cadastro central de todas as pessoas e entidades que se relacionam com o fundo.

| Funcionalidade | Descrição |
|---------------|-----------|
| CRUD de favorecidos | Participante, patrocinador, instituidor, fornecedor, prestador |
| Validação fiscal | CPF/CNPJ com dígito verificador, consulta à Receita Federal (via integração) |
| Dados bancários | Múltiplas contas por favorecido, chave PIX, validação de agência/conta |
| Endereço | Via CEP automático, múltiplos endereços por tipo (cobrança, correspondência) |
| Contatos | E-mail, telefone, whatsapp com indicação de preferencial |
| Vínculo a planos | Um favorecido pode estar vinculado a múltiplos planos com papéis diferentes |
| Documentos digitais | Upload de RG, CPF, comprovante de residência com OCR |
| Autocomplete | Busca rápida por nome, CPF/CNPJ para outros módulos consumirem |

**Eventos que publica:**
- `FavorecidoCriado` / `FavorecidoAlterado` — consumido por outros serviços
- `FavorecidoVinculoAlterado` — mudança de vínculo com plano

**Melhorias de negócio incorporadas (seção 6 do domínio):**
- (6.5) Portal do participante com autosserviço de atualização cadastral
- (6.12) Gestão de documentos com OCR

#### gestao-planos

**Responsabilidade:** Configuração e gestão de planos de benefício.

| Funcionalidade | Descrição |
|---------------|-----------|
| Cadastro de planos | CD, BD, CV com parametrização completa |
| Associação patrocinadores/instituidores | Quem patrocina cada plano |
| Perfis de investimento | Alocação por perfil (conservador, moderado, agressivo) |
| Convênios bancários | Contas vinculadas a cada plano |
| Vigência | Planos ativos, encerrados, em implantação |

**Eventos que publica:**
- `PlanoCriado` / `PlanoConfigurado`
- `PlanoPerfilInvestimentoAlterado`

#### instituicao-financeira

**Responsabilidade:** Catálogo de bancos, agências e convênios.

| Funcionalidade | Descrição |
|---------------|-----------|
| Catálogo de bancos | COMPE, nome, APIs suportadas (BB, Bradesco, Itaú, Santander) |
| Agências | Vinculadas a bancos com endereço |
| Convênios bancários | Contas correntes e de investimento por plano, limites, tarifas |
| Saldo | Consulta de saldo online (via API bancária) |
| Extrato | Importação automática de extratos |
| Tarifas | Registro e comparação de tarifas bancárias por convênio |

**Melhorias de negócio incorporadas:**
- (6.8) Central de Convênios — visão consolidada de todas as contas bancárias, gestão de tarifas

### 3.2. Core Domain — Tesouraria

#### tesouraria-operacoes

**Responsabilidade:** O coração da tesouraria — lançamentos, baixas, estornos, remessas.

| Funcionalidade | Descrição |
|---------------|-----------|
| Lançamento simples | Débito/crédito com natureza financeira, centro de custo, histórico |
| Lançamento contábil | Partidas dobradas (débito + crédito) |
| Lançamento de receita | Contribuições, aportes |
| Lançamento de despesa | Benefícios, pagamentos a fornecedores |
| Baixa | Marcação de lançamento como pago |
| Baixa parcial | Pagamento fracionado |
| Estorno | Reversão de lançamento (com auditoria) |
| Remessa bancária | Geração de arquivo de remessa (CNAB400/700/750) |
| Retorno bancário | Leitura de arquivo de retorno e baixa automática |
| PIX | Integração com PIX para pagamentos |
| Workflow de aprovação | Alçadas por valor, múltiplas assinaturas |
| Dashboard operacional | Contas a pagar, a receber, fluxo de hoje |

**Eventos que publica:**
- `LancamentoCriado` / `LancamentoBaixado` / `LancamentoEstornado`
- `RemessaEnviada` / `RemessaRetornada` / `RemessaCancelada`
- `PagamentoAprovado`

**Melhorias de negócio incorporadas:**
- (6.2) Workflow de aprovação com alçadas e múltiplas assinaturas
- (6.3) Gestão de liquidez com projeção de fluxo de caixa (integrado a este módulo)
- (6.12) Gestão de documentos vinculados a lançamentos

#### conciliacao-bancaria

**Responsabilidade:** Confrontação automática entre lançamentos internos e extratos bancários.

| Funcionalidade | Descrição |
|---------------|-----------|
| Importação de extratos | OFX, CSV (múltiplos bancos), API bancária direta |
| Motor Fitid 2.0 | Algoritmo de casamento com aprendizado de padrões |
| Regras de conciliação | Configuráveis por tipo de lançamento, banco, faixa de valor |
| Dashboard de exceções | Agrupamento inteligente por tipo de divergência |
| Conciliação em lote | Aceitar/rejeitar exceções em grupo |
| Rastreamento | Linha do tempo de cada item conciliado |
| Saldo inicial | Abertura de período para conciliação |
| Conciliação de investimentos | Posições de custodiantes vs. esperado |

**Eventos que publica:**
- `ConciliacaoRealizada` / `ExcecaoIdentificada`
- `MovimentoNaoConciliado` — divergência não resolvida automaticamente

**Melhorias de negócio incorporadas:**
- (6.4) Conciliação com aprendizado de padrões — quanto mais usada, mais automática
- (6.10) Conciliação de investimentos com administradores

#### integracao-bancaria

**Responsabilidade:** Gateway centralizado de integração com instituições financeiras.

| Funcionalidade | Descrição |
|---------------|-----------|
| Transferências | TED/DOC/PIX para múltiplos bancos |
| Boletos | Geração, registro, baixa de boletos |
| DARF | Geração e pagamento de tributos federais |
| GPS | Guias da Previdência Social |
| PIX | Cobrança e transferência PIX |
| Extrato bancário | Consulta de extratos via API |
| Múltiplos bancos | BB, Bradesco, Itaú, Santander, bancos digitais |
| Rate limiting | Controle de chamadas por banco |
| Retry com backoff | Reenvio automático em caso de falha |

**Observação:** Cada banco tem seu próprio adaptador. A API do módulo é unificada — o tenant escolhe os bancos que usa.

### 3.3. Core Domain — Contabilidade

#### contabilidade (O mais complexo)

**Responsabilidade:** Escrituração contábil completa, fechamento, demonstrações.

| Funcionalidade | Descrição |
|---------------|-----------|
| Plano de contas | Estrutura hierárquica configurável por tenant |
| Fato gerador | Motor de parametrização: evento financeiro → partida contábil |
| Lote contábil | Agrupamento e validação de lançamentos contábeis |
| Histórico padrão | Textos parametrizáveis por combinação de lote + plano |
| Rateio contábil | Distribuição automática entre centros de custo |
| Disponível | Saldo contábil por plano + natureza financeira |
| Fechamento diário | Validação de partidas dobradas do dia |
| Fechamento mensal | Encerramento do período: resultado, encerramento de contas |
| Consolidação | Fechamento único consolidando todos os planos |
| Encerramento de exercício | Fechamento anual com transporte de saldos |
| Reabertura | Reabertura de período (com controle de auditoria) |
| Balancete | Relatório de saldos por período |
| Razão | Detalhamento de movimentação por conta |
| Diário | Livro diário contábil |
| Demonstrações | DRE, balanço patrimonial, notas explicativas |

**Eventos que publica:**
- `FechamentoRealizado` / `FechamentoConsolidado`
- `FatoGeradorProcessado`
- `DisponivelAlterado`

**Melhorias de negócio incorporadas:**
- (6.1) Motor de regras de custeio (integrado com contabilidade)
- (6.7) Orquestração inteligente de ciclo contábil com pipeline autoexecutável

### 3.4. Core Domain — Investimentos

#### investimentos-cotas

**Responsabilidade:** Gestão de investimentos, cálculo de cotas, perfis.

| Funcionalidade | Descrição |
|---------------|-----------|
| Perfis de investimento | Cadastro e configuração por plano |
| Aplicação | Aporte de recursos em perfil |
| Resgate | Retirada de recursos de perfil |
| Cálculo de cota | Recálculo periódico do valor da cota |
| Histórico de cota | Série histórica com memória de cálculo detalhada |
| Posição atual | Snapshot da posição por perfil/plano |
| Conciliação com custodiantes | Posição esperada vs. informada |
| Rentabilidade | Cálculo de retorno por período |

**Eventos que publica:**
- `CotaRecalculada` / `AplicacaoRealizada` / `ResgateProcessado`
- `PosicaoAtualizada`

**Melhorias de negócio incorporadas:**
- (6.10) Conciliação de investimentos com custodiantes

### 3.5. Core Domain — Custeio

#### custeio

**Responsabilidade:** Regras de contribuição, rateios, PGA.

| Funcionalidade | Descrição |
|---------------|-----------|
| Motor de regras de custeio | Fórmulas configuráveis pelo negócio |
| Custeio administrativo | Taxa de administração por plano |
| PGA | Plano de Gestão Administrativa |
| Rateio | Distribuição de custos entre planos e centros de custo |
| Simulação | Cenários "what-if" de alteração de alíquota |
| Precificação | Análise de margem por plano |

**Eventos que publica:**
- `CusteioCalculado` / `RateioProcessado`
- `MargemPlanoAtualizada`

**Melhorias de negócio incorporadas:**
- (6.1) Motor de regras de custeio configurável pelo negócio
- (6.9) Precificação de planos por margem

### 3.6. Supporting Domain — Obrigações Fiscais

#### obrigacoes-fiscais

**Responsabilidade:** Geração e gestão de obrigações tributárias e acessórias.

| Funcionalidade | Descrição |
|---------------|-----------|
| EFD | Geração automática do arquivo de Escrituração Fiscal Digital |
| REINF | Geração mensal de retenções e informações previdenciárias |
| PIS/COFINS | Cálculo por regime (cumulativo/não-cumulativo) |
| Retenções | Cálculo de IR, CSLL, PIS, COFINS, INSS na fonte |
| Tabelas fiscais | Atualização automática de alíquotas (governo federal) |
| Dashboard fiscal | Exposição fiscal por plano, multas potenciais evitadas |
| Compliance em tempo real | Validação antes do pagamento |

**Eventos que publica:**
- `EFDGerado` / `REINFGerado`
- `AlertaFiscal` — retenção incorreta detectada

**Melhorias de negócio incorporadas:**
- (6.6) Gestão de riscos fiscais em tempo real

### 3.7. Generic Domain — Plataforma e Suporte

#### importacao-dados

**Responsabilidade:** Importação de folhas de pagamento, arquivos bancários e cargas.

| Funcionalidade | Descrição |
|---------------|-----------|
| Folha de pagamento | Importação de contribuições de sistemas de RH |
| Retorno bancário | Leitura de arquivos CNAB de retorno |
| Extrato OFX | Importação de extratos de múltiplos bancos |
| Carga inicial | Migração de dados de legados (SIS.SP, Excel) |
| Validação | Regras de consistência pré-importação |
| Log de carga | Auditoria completa de cada importação |

#### exportacao-relatorios

**Responsabilidade:** Geração de relatórios e exportações em múltiplos formatos.

| Funcionalidade | Descrição |
|---------------|-----------|
| Relatórios contábeis | Balancete, razão, diário em PDF/XLS |
| Demonstrativos | DRE, balanço patrimonial |
| Relatórios gerenciais | Fluxo de caixa, contas a pagar/receber |
| Exportação de dados | CSV, XLS, JSON via API |
| Relatórios regulatórios | PREVIC, CVM |

#### gestao-documentos

**Responsabilidade:** Gestão de documentos digitais vinculados a operações.

| Funcionalidade | Descrição |
|---------------|-----------|
| Upload de documentos | Vinculado a lançamentos, remessas, favorecidos |
| OCR | Extração automática de dados de notas fiscais e boletos |
| Workflow de aprovação | Aprovação documental vinculada a pagamento |
| Repositório auditável | Retenção por prazo legal |
| Assinatura digital | Integração com ZapSign, Clicksign |

#### notificacoes

**Responsabilidade:** Central de comunicações do sistema.

| Funcionalidade | Descrição |
|---------------|-----------|
| E-mail transacional | Aprovações pendentes, alertas de saldo |
| Notificação in-app | Centro de notificações no sistema |
| WhatsApp | Alertas críticos para aprovadores |
| Preferências | Cada usuário configura seus canais |

#### analytics-bi

**Responsabilidade:** Inteligência de negócio e benchmarking.

| Funcionalidade | Descrição |
|---------------|-----------|
| Dashboards gerenciais | KPIs por plano, tenant, período |
| Benchmarking anônimo | Comparação com fundos similares |
| Detecção de anomalias | IA para identificar padrões suspeitos em lançamentos |
| Exportação de dados | Para ferramentas externas (Power BI, Metabase) |

**Melhorias de negócio incorporadas:**
- (6.3) Gestão de liquidez (dashboards)
- (6.5) Portal do participante (relatórios de saldo)

---

## 4. Plano de Migração de Dados

### 4.1. Estratégia Geral

```
┌──────────────────────────────────────────────────────────┐
│                    ESTRATÉGIA DE MIGRAÇÃO                │
├────────────┬──────────────┬────────────┬─────────────────┤
│  Período   │  Estratégia  │  Dados     │  Risco          │
├────────────┼──────────────┼────────────┼─────────────────┤
│ Mês 1-2    │  Shadow Mode │ Nenhum     │ Baixo           │
│            │  (novos      │ migrado    │                 │
│            │  cadastros   │            │                 │
│            │  já caem no  │            │                 │
│            │  novo)       │            │                 │
├────────────┼──────────────┼────────────┼─────────────────┤
│ Mês 3-4    │  Migração    │ Cadastro   │ Médio           │
│            │  seletiva    │ + planos   │                 │
├────────────┼──────────────┼────────────┼─────────────────┤
│ Mês 5-6    │  Migração    │ 3 anos     │ Alto            │
│            │  histórica   │ de lanc.   │                 │
│            │  + saldos    │ + saldos   │                 │
├────────────┼──────────────┼────────────┼─────────────────┤
│ Mês 7+     │  Operação    │ Tempo real │ Controlando     │
│            │  dual        │ via        │                 │
│            │  (strangler) │ eventos    │                 │
└────────────┴──────────────┴────────────┴─────────────────┘
```

### 4.2. Plano Detalhado por Fase

#### Fase 1 — Shadow Mode (Mês 1-2)

O sistema legado continua sendo o sistema de registro. O novo SaaS roda em paralelo recebendo uma cópia dos dados via eventos.

```
Legado (produção) ──→ Eventos de domínio ──→ SaaS (shadow) ──→ Validação
                                                                    │
                                                                    ▼
                                                            Relatório de
                                                            divergências
```

- Nenhum dado é migrado ainda
- O SaaS recebe eventos do legado e popula suas tabelas
- Ao final de cada dia, um relatório de divergências compara: legado vs. SaaS (total de lançamentos, saldos contábeis)
- Equipe valida e corrige bugs até divergência < 0,1%
- **Ponto de decisão:** divergência abaixo de 0,1% por 30 dias consecutivos → avança para Fase 2

#### Fase 2 — Migração de Cadastro (Mês 3-4)

```
ETL Pipeline (offline, fim de semana):
┌────────────┐    ┌──────────────┐    ┌──────────────┐
│  Legado    │───→│  Mapper      │───→│  SaaS        │
│  Favorecido│    │  (CPF/CNPJ   │    │  Favorecido  │
│  Plano     │    │   normaliza, │    │  Plano       │
│  Banco     │    │   dedup)     │    │  Banco       │
└────────────┘    └──────────────┘    └──────────────┘
```

1. Exporta dados de favorecidos, planos, bancos do legado
2. Roda pipeline de limpeza (dedup por CPF/CNPJ, normalização de endereços)
3. Importa no SaaS (via API ou carga direta no banco)
4. Valida contagem: mesma quantidade de favorecidos ativos
5. A partir deste momento, novos cadastros são feitos APENAS no SaaS

**Ponto de decisão:** 100% dos cadastros migrados e validados, time operacional treinado no novo sistema de cadastro → avança.

#### Fase 3 — Migração Histórica (Mês 5-6)

Dados financeiros são os mais críticos. Estratégia de migração sem risco:

```
1. Exporta lançamentos dos últimos 3 anos do legado
2. Processa em lotes (10.000 registros)
3. Para cada lote:
   a. Importa no SaaS
   b. Calcula saldo contábil no SaaS
   c. Compara com saldo contábil no legado
   d. Se divergir → lote rejeitado, investigação manual
4. Ao final: saldo de abertura do período corrente
5. Valida: saldo contábil consolidado = legado

CRITÉRIO DE SUCESSO:
  │ 100% dos lotes importados
  │ 100% dos saldos conferem com o legado
  │ Tempo total de migração: < 48h (fim de semana)
  ▼
```

**Risco controlado:** se a migração falhar, desfaz-se em minutos (database-per-tenant: só dropar o banco e tentar de novo).

**Ponto de decisão:** saldos batem, time de contabilidade valida os relatórios → avança.

#### Fase 4 — Operação Dual (Mês 7+)

```
            ┌──────────────────────┐
            │  Legado (read-only)  │ ←─── histórico disponível para consulta
            │  Contabilidade       │
            │  (último módulo)     │
            └──────────────────────┘

            ┌──────────────────────┐
            │  SaaS (escrita)      │ ←─── todos os novos lançamentos
            │  Cadastro            │
            │  Tesouraria          │
            │  Conciliação         │
            └──────────────────────┘
```

- Novas operações (lançamentos, remessas, pagamentos) são feitas APENAS no SaaS
- Legado mantido em read-only para consulta de dados históricos (+3 anos)
- Migração dos saldos contábeis abertos: saldo do mês anterior transferido como saldo inicial no SaaS
- Último módulo a sair do legado: **contabilidade**, devido à complexidade do fechamento

**Ponto de decisão:** 90 dias de operação estável no SaaS, sem divergências → agenda desligamento do legado.

### 4.3. Pontos de Rollback

Cada fase tem um **ponto de rollback** explícito:

| Fase | Gatilho de rollback | Ação | Tempo de reversão |
|------|--------------------|------|-------------------|
| Shadow | Divergência > 0,5% por 7 dias | Desliga shadow, investiga | 1 hora |
| Migração cadastro | Contagem de registros difere | Drop das tabelas migradas, re-exporta | 2 horas |
| Migração histórica | Saldo contábil diverge | Drop do banco do tenant, reimporta | 4 horas |
| Operação dual | Bug crítico em produção | Volta escrita para legado, SaaS vira shadow | 30 minutos |

---

## 5. Plano de Incorporação das Melhorias de Negócio

Cada melhoria proposta na seção 6 do documento de domínio deve ser construída como parte da reescrita, não adicionada depois. Abaixo, o cronograma de entrega:

### Fase 1 — MVP (Meses 1-6): Melhorias essenciais inclusas

| Melhoria | Módulo | Esforço | Prioridade |
|----------|--------|---------|-----------|
| (6.5) Portal do participante | cadastro-favorecido | 3 sprints | Essencial — sem portal, o SaaS não se diferencia |
| (6.2) Workflow de aprovação | tesouraria-operacoes | 2 sprints | Essencial — risco operacional sem aprovação |
| (6.8) Central de convênios | instituicao-financeira | 1 sprint | Rápido e agrega valor imediato |

### Fase 2 — Expansão (Meses 7-12): Melhorias competitivas

| Melhoria | Módulo | Esforço | Prioridade |
|----------|--------|---------|-----------|
| (6.1) Motor de regras de custeio | custeio | 4 sprints | Alto — diferencia o SaaS de concorrentes |
| (6.4) Conciliação com aprendizado | conciliacao-bancaria | 3 sprints | Alto — redução de horas de conciliação |
| (6.7) Orquestração de ciclo contábil | contabilidade | 3 sprints | Alto — previsibilidade no fechamento |
| (6.6) Compliance fiscal em tempo real | obrigacoes-fiscais | 2 sprints | Alto — evita multas |

### Fase 3 — Aceleração (Meses 13-18): Melhorias de retenção

| Melhoria | Módulo | Esforço | Prioridade |
|----------|--------|---------|-----------|
| (6.3) Gestão de liquidez | tesouraria-operacoes + analytics-bi | 3 sprints | Médio — projeção de fluxo |
| (6.9) Precificação por margem | custeio | 2 sprints | Médio — sustentabilidade |
| (6.10) Conciliação de investimentos | conciliacao-bancaria + investimentos-cotas | 3 sprints | Médio — precisão |
| (6.11) Simulação atuarial | custeio + analytics-bi | 4 sprints | Baixo — nicho |
| (6.12) Gestão de documentos | gestao-documentos | 2 sprints | Médio — compliance documental |

---

## 6. Equipe e Cronograma

### 6.1. Times Necessários

```
FASE 1 (Meses 1-6) — MVP com 3 squads:

Squad A (5 devs): Cadastro + Planos + Instituição Financeira
Squad B (5 devs): Tesouraria (lançamentos + remessas) + Conciliação
Squad C (3 devs): Plataforma (multi-tenancy, auth, billing, infra)

Compartilhados:
  1 Tech Lead (arquitetura geral)
  1 Product Manager (priorização + clientes piloto)
  1 Designer (UX do portal do participante)
  1 DevOps

Total Fase 1: 17 pessoas

FASE 2 (Meses 7-12) — +2 squads:

Squad D (4 devs): Contabilidade (fato gerador, fechamento, balancete)
Squad E (3 devs): Obrigações Fiscais + Custeio

Compartilhados adicionais:
  2 Sucesso do Cliente (onboarding dos novos tenants)
  1 Especialista de Domínio Contábil

Total Fase 2: 27 pessoas

FASE 3 (Meses 13-18) — +1 squad:

Squad F (3 devs): Investimentos + BI + Documentos

Compartilhados adicionais:
  2 Vendas / Pré-vendas
  1 Compliance Regulatório

Total Fase 3: 33 pessoas
```

### 6.2. Cronograma Consolidado

```
Mês:   1  2  3  4  5  6   |  7  8  9 10 11 12  | 13 14 15 16 17 18
                          |                     |
MVP:   ████████████████████|                     |
  Cadastro    ████████████ |                     |
  Tesouraria     ████████████████|               |
  Conciliação        ████████████|               |
  Plataforma  ████████████ |                     |
  Portal part.   ████████████████|               |
  Workflow apr.     ████████|                    |
                          |                     |
EXPANSÃO:                 |████████████████████ |
  Contabilidade           |████████████████     |
  Custeio/Motor           |   ██████████████     |
  Conciliação aprendizado |   ████████████      |
  Compliance fiscal       |     ████████████    |
  Ciclo contábil          |       ██████████████|
                          |                     |
ACELERAÇÃO:               |                     |████████████████████
  Liquidez                |                     |████████████
  Investimentos           |                     |   ████████████
  Documentos              |                     |     ████████
  Precificação            |                     |       ████████
  Simulação atuarial      |                     |         ████████████
                          |                     |
CLIENTES:                 |                     |
  Piloto (dataa)   ●●●●●●|                     |
  Cliente 2               |     ●               |
  Cliente 3               |         ●           |
  Cliente 4-5             |             ●●      |
  Cliente 6-10            |                 ●●●●|●●●●●
  Cliente 11-20           |                     |     ●●●●●●●●●●
                          |                     |
MÉTRICAS:                 |                     |
  MRR:           0   0  20k 40k 60k 80k |100k 120k 150k 180k 200k 250k |300k 350k 400k 450k 500k 600k
  Clientes:      0   0   1   1   1   1  |  2    3    4    5    6    8  | 10   12   15   18   22   25
```

### 6.3. Marcos de Decisão (Go/No-Go)

| Marco | Mês | Critério para avançar |
|-------|-----|----------------------|
| **M1** | Mês 1 | Shadow mode rodando, divergência < 0,5% |
| **M2** | Mês 3 | Cadastro migrado, operação rodando em SaaS |
| **M3** | Mês 6 | MVP completo, dataa operando em SaaS, 2º cliente onboard |
| **M4** | Mês 9 | Contabilidade rodando em paralelo, divergência zero |
| **M5** | Mês 12 | Legado read-only, 6+ clientes ativos, NPS > 40 |
| **M6** | Mês 15 | Legado desligado, 15+ clientes, churn < 2% |
| **M7** | Mês 18 | 25+ clientes, ARR > R$ 7M, plataforma estável |

---

## 7. Riscos da Reescrita

### 7.1. Análise de Riscos

| Risco | Prob. | Impacto | Mitigação |
|-------|-------|---------|-----------|
| **Equipe não conhece o domínio** | Alta | Crítico | 1 especialista de domínio dedicado ao time (ex-dev do legado ou analista de negócios) |
| **Regras de negócio não documentadas** | Alta | Alto | Engenharia reversa das actions antes de reescrever; gravação de sessões com usuários-chave |
| **Second-system effect** (excesso de complexidade) | Média | Alto | MVP enxuto definido por marcos Go/No-Go; cada sprint pergunta: "o mínimo para entregar valor?" |
| **Perda de dados na migração** | Média | Crítico | Database-per-tenant permite drop e retry; perímetro de validação automática |
| **Resistência de usuários** | Alta | Alto | Envolvimento de usuários-chave desde o Mês 1; shadow mode cria confiança |
| **Subestimação da contabilidade** | Média | Alto | Contabilidade é o módulo mais complexo; squad dedicado desde o Mês 1 fazendo engenharia reversa |
| **Mudança regulatória durante a reescrita** | Alta | Médio | Legado mantido operacional até Fase 3; time de compliance acompanha mudanças |

### 7.2. O Que NÃO Fazer (Anti-padrões)

- ❌ **Copiar regras de negócio do legado linha por linha** — cada regra precisa ser entendida e validada com o negócio. Apenas 30% das regras de um sistema legado ainda são relevantes.
- ❌ **Reescrever tudo em monolito e depois quebrar** — o sistema novo já nasce modular (microsserviços por contexto delimitado).
- ❌ **Mudar tecnologia só por moda** — Java 21+ com Spring Boot é a escolha certa para este domínio. Não trocar por linguagem exótica.
- ❌ **Aceitar customização por código para cada cliente** — o modelo SaaS exige que customizações sejam configuráveis. Se um cliente pede algo fora da parametrização, a resposta é "roda no legado até a plataforma suportar".
- ❌ **Fazer big-bang migration** — estrangulamento progressivo é a única abordagem segura. Cada módulo migrado individualmente.

---

## 8. Próximos Passos Imediatos

### Mês 0 — Pré-projeto (Agora)

| Atividade | Responsável | Prazo |
|-----------|-------------|-------|
| 1. Apresentar este plano para stakeholders | Tech Lead + PM | 1 semana |
| 2. Identificar 2 usuários-chave do legado para serem "domain experts" no time de reescrita | PM | 1 semana |
| 3. Provisionar infraestrutura de desenvolvimento (K8s, banco, CI/CD) | DevOps | 2 semanas |
| 4. Criar repositórios do novo sistema (monorepo com módulos) | Tech Lead | 1 semana |
| 5. Setup do shadow mode: configurar eventos do legado para o novo sistema | Squad C + DevOps | 3 semanas |
| 6. Engenharia reversa do módulo de cadastro (favorecido) | Squad A | 2 semanas |
| 7. Kickoff do time e alinhamento de expectativas | Tech Lead + PM | 1 dia |

### Mês 1 — Primeira Sprint

| Atividade | Squad |
|-----------|-------|
| Shadow mode operacional (eventos de favorecido chegando no novo sistema) | C |
| Primeira versão do cadastro de favorecido (API REST + banco) | A |
| Primeira versão do tenant-registry (provisionamento manual) | C |
| Primeira versão do portal do participante (consulta de dados cadastrais) | A + UX |
| Engenharia reversa do módulo de lançamentos financeiros | B |

---

## 9. Resumo Executivo

```
O QUE:    Reescrever o dataa-tesouraria como um SaaS multi-tenant moderno
          para fundos de pensão (EFPCs), incorporando 12 melhorias de
          negócio desde o primeiro dia.

COMO:     Estrangulamento progressivo do monolito legado → microsserviços
          por contexto delimitado → database-per-tenant → 6 fases de
          migração controlada.

QUEM:     3 squads no início, crescendo para 6 squads (33 pessoas) no
          pico da Fase 3.

QUANDO:   18 meses do kickoff ao desligamento do legado, com marcos
          trimestrais Go/No-Go.

RISCO:    Controlado: shadow mode valida dados antes da migração;
          database-per-tenant permite rollback em minutos; legado
          mantido como contingência até o Mês 15.

RESULTADO:
  ├── SaaS multi-tenant com 3 tiers de precificação
  ├── 15 microsserviços independentes
  ├── Portal do participante com autosserviço
  ├── Conciliação com aprendizado de padrões (92% de automação)
  ├── Motor de regras de custeio configurável pelo negócio
  ├── Compliance fiscal em tempo real
  ├── Workflow de aprovação com alçadas
  ├── Benchmarking entre fundos
  └── 25+ clientes em 18 meses, ARR > R$ 7M
```

---

*Documento gerado em 2026-06-22*
*Plano de reescrita para SaaS — dataa-tesouraria*
