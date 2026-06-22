# Plano de Produto — ClearPension

## Um SaaS do Zero para Competir com os Sistemas Legados de Fundos de Pensão

---

## 0. Filosofia: Por que este produto existe

O mercado brasileiro de softwares para fundos de pensão (EFPCs) é dominado por sistemas que foram construídos nos anos 90 e 2000 — monolitos gigantes em tecnologias como Delphi, Clarion, Java legado com 2.767 classes, 30 domínios acoplados e 0,05% de cobertura de testes. Estes sistemas:

- Cobram caro (muitas vezes 1-2% do patrimônio do fundo)
- São difíceis de integrar (APIs raras ou inexistentes)
- Tratam o participante como um número de CPF, não como um cliente
- Não oferecem inteligência de negócio embarcada
- São atualizados uma ou duas vezes por ano

**ClearPension não é uma reescrita destes sistemas. É um concorrente que ataca de outro ângulo:**

| Eles | Nós |
|------|-----|
| Construídos para o backoffice | Construídos para o participante |
| Monolitos fechados | Plataforma aberta com API pública |
| Atualizações trimestrais | Deploy contínuo (semanas, não meses) |
| Precificação por patrimônio | Precificação por participante ativo |
| Vendas consultivas longas | Self-service onboarding |
| Dados presos no sistema | Dados exportáveis + open finance |
| Foco em contabilidade | Foco em experiência do participante |
| Feature-driven | Data-driven (IA desde o dia 1) |

**Não vamos copiar o modelo mental do legado. Vamos reimaginar o que um fundo de pensão precisa em 2026+.**

---

## 1. Nicho e Estratégia de Entrada

### 1.1. Oportunidade Real

O mercado de EFPCs no Brasil tem ~280 entidades com R$ 1,2 tri em ativos. Mas existem outros mercados adjacentes que os sistemas legados ignoram:

| Mercado | Quantidade | Potencial |
|---------|-----------|-----------|
| EFPCs (fundos de pensão) | ~280 | R$ 1,2 tri em ativos |
| EAPC (entidades abertas) | ~80 | R$ 200 bi |
| Planos de saúde (autogestão) | ~150 | R$ 50 bi |
| Fundos multipatrocinados | ~40 | Crescentes |
| Clubes de investimento | ~5.000 | Potencial de expansão |
| Family offices | ~2.000 | Alta renda |

**Estratégia de entrada:** Não começar pelas EFPCs grandes (dominadas pelos incumbentes). Entrar pelas **EFPCs médias/pequenas insatisfeitas** e pelos **fundos multipatrocinados** (estrutura mais moderna, menos presas a sistemas legados).

### 1.2. Perfil do Cliente Ideal (ICP)

```
Porte:     R$ 100M - R$ 5B em ativos
dor:       Sistema atual é caro e não oferece portal ao participante
Perfil:    Já tentou trocar de sistema ou está avaliando
Região:    Sudeste e Sul (maior densidade de EFPCs)
Decisor:   Diretor financeiro / Superintendente (não TI)
Orçamento: R$ 5k - R$ 25k/mês
O que quer: "Um sistema moderno que meus participantes possam acessar pelo celular"
```

---

## 2. Domínios do Novo Produto (Zero Relação com Legado)

Nada de "favorecido", "lançamento", "remessa", "fato gerador" como conceitos primitivos. Nosso modelo mental é outro.

### 2.1. Core Domain — Gestão Financeira Simplificada

#### members (Membros / Stakeholders)

Uma pessoa ou entidade que se relaciona financeiramente com o fundo. **Não é "favorecido"** — é um conceito que nasce mobile-first.

```
Member {
  id: UUID (não sequencial)
  type: participant | sponsor | provider | beneficiary
  identity: CPF | CNPJ | Passaporte
  profile: { name, email, phone, avatar }
  authentication: { selfie, biometric, passwordless }
  preferences: { channel, notifications, language }
  wallet: { bankAccounts[], pixKeys[] }
  documents: { id, selfie, proofOfAddress, contract }
  status: active | suspended | pending | archived
  engagement: { lastLogin, npsScore, satisfaction }
  createdAt, updatedAt
}
```

#### funds (Fundos / Planos)

Diferente de "plano de benefícios". Um **fund** pode ser um plano de pensão, um fundo de investimento, um clube, um family office.

```
Fund {
  id: UUID
  type: pensionCd | pensionBd | pensionCv | investmentClub | familyOffice
  sponsor: Member (company or institution)
  rules: {
    contributionFormula (DSL)
    vestingPeriod: number
    retirementAge: number
    benefitFormula (DSL)
  }
  governance: { board[], committees[], bylaws }
  investmentPolicy: { profiles[], benchmarks[], limits }
  bankAccounts: { operational, investment }
  status: active | frozen | liquidating
}
```

#### transactions (Movimentações Financeiras)

Não é "lançamento", não tem "débito/crédito" como conceito primitivo. É um **evento financeiro imutável** em um stream de eventos.

```
Transaction {
  id: UUID
  streamId: UUID (aggregate root — fund, member, account)
  type: contribution | benefit | fee | transfer | investment | tax
  amount: { value, currency }
  direction: inflow | outflow
  counterparty: Member (quem pagou/recebeu)
  allocation: { fundId, costCenter, category }
  settlement: { method: pix | ted | boleto | darf, date, status }
  accounting: { journalRule, accounts[] }
  metadata: { invoice, contract, approval }
  parentId: UUID (para splits, reversals)
  createdAt (imutável)
}
```

**Regra de ouro:** Uma vez criada, uma transaction NUNCA é alterada. Estornos criam novas transactions com `parentId` apontando para a original. O saldo é calculado somando o stream.

#### payment-orders (Ordens de Pagamento)

Não é "remessa". É uma ordem de pagamento desacoplada do batch bancário.

```
PaymentOrder {
  id: UUID
  transactions: Transaction[]
  method: pix | ted | darf | gps | boleto
  bankRoute: {
    institution, agency, account
    pixKey (se PIX)
  }
  schedule: { requestedDate, cutoffTime }
  approval: { level, approvers[], signatures[] }
  status: draft | pendingApproval | approved | sent | confirmed | failed | cancelled
  execution: { sentAt, confirmedAt, bankReturn }
  risk: { fraudScore, complianceCheck }
}
```

#### reconciliation-stream (Conciliação Contínua)

Diferente de "fitid" que roda em batch. É um stream contínuo de conciliação.

```
ReconciliationStream {
  id: UUID
  bankAccount: { institution, agency, account }
  period: { startDate, endDate }
  expectedTransactions: Transaction[]
  bankTransactions: ImportedStatement[]
  matches: Match[]
  exceptions: Exception[]
  status: reconciling | partial | complete | confirmed
  autoMatchRate: number (ML melhora isso ao longo do tempo)
}

Match {
  transactionId, statementLineId
  confidence: 0.0-1.0
  method: exact | fuzzy | manual
  matchedAt
}
```

### 2.2. Domínio Novo — participant-engagement

Não existe no sistema legado. É o coração do nosso produto.

#### participant-app

Aplicativo mobile (React Native / Flutter) onde o participante:

- **Vê o saldo** em tempo real (não precisa esperar extato mensal)
- **Simula aposentadoria** com cenários (idade, contribuição extra, rentabilidade)
- **Atualiza dados** (endereço, conta bancária, chave PIX) sem burocracia
- **Envia documentos** (selfie, comprovante) com OCR e validação automática
- **Acompanha solicitações** (portabilidade, resgate, revisão de benefício)
- **Recebe notificações** push sobre pagamentos, aportes, convocações
- **Educação financeira** com conteúdos personalizados por fase de vida
- **Gamificação** — metas de contribuição, selos de engajamento

#### nps-loop

Pesquisas de satisfação embedadas no fluxo do aplicativo:

- Após consultar saldo: "Em uma escala de 0-10, o quanto você confia na gestão do seu fundo?"
- Após solicitar portabilidade: "Quão fácil foi realizar esta solicitação?"
- Após receber benefício: "O valor do benefício atende suas expectativas?"

Os dados alimentam um **dashboard de saúde do relacionamento** que o fundo nunca teve antes.

### 2.3. Domínio Novo — governance-hub

Gestão de governança corporativa do fundo — outro mercado que o legado ignora.

| Funcionalidade | Descrição |
|---------------|-----------|
| **Board management** | Convocações, pautas, atas, votação online de reuniões do conselho deliberativo |
| **Committee workflows** | Comitê de investimentos, comitê de elegibilidade, comitê de benefícios |
| **Termo de posse** | Gestão de mandatos, vigência, documentação de conselheiros |
| **Votação remota** | Assinatura digital, quórum, registro imutável |
| **Prestação de contas** | Relatórios anuais, demonstrações contábeis, parecer do conselho fiscal |
| **Regulatório** | Minutas de assembleia, registros PREVIC |

**Por que ninguém faz isso?** Porque os sistemas legados nunca saíram do backoffice financeiro. É um mercado adjacente inteiro sem concorrência digital.

### 2.4. Domínio Novo — intelligence-layer

Inteligência artificial embarcada, não um módulo separado.

#### anomaly-detector

ML treinado para detectar padrões suspeitos em transações financeiras:

- Pagamentos duplicados (mesmo valor, mesmo favorecido, próxima data)
- Valores fora do padrão histórico (ex: benefício 3x maior que a média do plano)
- Sequências suspeitas (múltiplos pagamentos pequenos no mesmo dia)
- Mudança de conta bancária seguida de pagamento
- Cross-tenant anomalias: "este padrão nunca foi visto em nenhum fundo similar"

#### cashflow-predictor

Modelo preditivo de fluxo de caixa:

- Previsão de entrada (contribuições esperadas baseadas em folha histórica)
- Previsão de saída (benefícios, fornecedores, obrigações fiscais)
- Recomendação de aplicação/resgate com base na necessidade projetada
- Cenários "what-if": "e se 10% dos participantes pedirem portabilidade?"

#### regulation-radar

Monitoramento contínuo de mudanças regulatórias:

- Scraping de diários oficiais (PREVIC, Receita Federal, BACEN)
- Impacto estimado em linguagem natural: "A IN PREVIC XX/2026 altera o prazo de fechamento de 15 para 10 dias úteis"
- Checklist de adequação: "seu fundo precisa ajustar X, Y e Z para estar em conformidade"
- Versionamento de regras de negócio: cada regra tem validade vinculada a uma norma

### 2.5. Domínio Novo — ecosystem-marketplace

Uma plataforma para terceiros construírem em cima da ClearPension.

| Participante | O que constrói |
|-------------|----------------|
| **Asset managers** | Dashboard de performance de fundos de investimento |
| **Auditorias** | Extração automática de dados para relatórios de auditoria |
| **Atuárias** | Simulações atuariais rodando em cima dos dados reais |
| **Bancos** | Ofertas de produtos financeiros para participantes (previdência privada, consórcio) |
| **Corretoras** | Recomendação de perfil de investimento |
| **Edtechs** | Cursos de educação financeira para participantes |
| **Lawtechs** | Automação de contratos e documentos jurídicos |

### 2.6. Domínio Novo — open-finance-hub

Integração com o ecossistema Open Finance Brasil:

- **Diretório de participantes**: conexão com instituições participantes
- **Iniciação de pagamento**: pagamentos via Open Finance (sem boleto bancário)
- **Compartilhamento de dados**: com consentimento do participante, dados de investimento podem ser compartilhados com outras instituições
- **Portabilidade**: facilitação da portabilidade de planos entre entidades

**Por que isso não existe?** Porque os sistemas legados não têm API e não conseguem participar do Open Finance.

### 2.7. Domínio Novo — cost-intelligence

Análise profunda de custos que o fundo nunca teve:

| Funcionalidade | Descrição |
|---------------|-----------|
| **Cost-per-member** | Custo administrativo detalhado por participante ativo |
| **Benchmark automático** | Comparação anônima com fundos similares (por porte, região, tipo de plano) |
| **Fee analyzer** | Análise de tarifas bancárias, taxas de administração, custódia |
| **Efficiency score** | Nota de eficiência operacional do fundo com recomendações |
| **What-if simulator** | "Se reduzirmos a taxa de adm em 0,1%, qual o impacto no saldo do participante?" |

---

## 3. Fluxos de Negócio Completamente Novos

### 3.1. Onboarding Digital do Participante

Diferente do legado (cadastro presencial ou por formulário em papel):

```
1. Patrocinador envia arquivo com dados dos novos participantes
2. Cada participante recebe link para criação de conta
3. Selfie + documento → biometria facial (validação em segundos)
4. Assinatura digital do termo de adesão
5. Indicação de conta bancária (via Open Finance, sem digitar)
6. Escolha do perfil de investimento (quiz de 5 perguntas)
7. Participante ativo em < 5 minutos
```

### 3.2. Fluxo de Pagamento com Prevenção a Fraudes

```
1. Operador cria uma PaymentOrder
2. ML calcula fraudScore baseado em:
   - Histórico do favorecido
   - Valor vs. média do plano
   - Conta bancária é nova?
   - Padrão sazonal
3. Se fraudScore > 70% → bloqueio automático + notificação compliance
4. Se fraudScore 40-70% → aprovação adicional requerida
5. Se fraudScore < 40% → fluxo normal de alçada
6. Após aprovações, executa pagamento via Open Finance ou banco
7. Transaction imutável registrada no event stream
```

### 3.3. Ciclo Contábil Automático (Sem "Fato Gerador")

Diferente do modelo mental de "fato gerador" (configuração complexa que poucos entendem):

```
1. Toda Transaction tem um type predefinido (contribution, benefit, fee, tax, transfer)
2. Cada type tem journal rules associadas (contas de débito/crédito)
3. No final do dia, as journal rules são aplicadas automaticamente
4. O sistema gera automaticamente as partidas contábeis
5. Se o plano de contas mudar, as regras são reaplicadas retroativamente
   (diferente do legado que exige estorno manual)

Benefício: O contador não precisa mais configurar "fato gerador"
           — o sistema deriva a contabilidade dos tipos de transação.
```

### 3.4. Conciliação em Tempo Real (Não Batch)

```
1. Transação é criada no sistema → status: pending
2. Pagamento é executado → aguardando confirmação bancária
3. Webhook do banco (ou PIX) confirma → transaction.status = settled
4. Conciliação feita sem intervenção humana
5. Apenas divergências viram exceção (extrato mostra algo que não passou pelo sistema)
```

---

## 4. Stack Tecnológica (Sem Nenhuma Relação com o Legado)

O legado: Java 8, Spring Boot, JPA/Hibernate, PostgreSQL, @Resource/@Autowired misturado, 2.767 classes.

**Nós:** Nada disso.

| Camada | Tecnologia | Por que |
|--------|-----------|---------|
| **API** | GraphQL (principal) + gRPC (eventos) | GraphQL permite consultas flexíveis (cada fundo tem necessidades diferentes); gRPC para streams de conciliação |
| **Linguagem** | Rust (core financeiro) / TypeScript (API layer) | Rust para o motor de transações imutáveis (performance + segurança de memória); TS para produtividade nas camadas de API |
| **Event Store** | EventStoreDB (transações) + Kafka (eventos de domínio) | Transações são append-only em EventStoreDB; domain events em Kafka para outros serviços |
| **Query/Read** | Materialized views em PostgreSQL + Redis | CQRS: writes vão para EventStoreDB, reads vêm de materialized views |
| **Banco analítico** | ClickHouse | Dashboards, BI, benchmark entre fundos — consultas OLAP rápidas |
| **ML / IA** | Python (modelos) + ONNX Runtime (inferência em Rust) | Treino em Python, inferência em Rust (latência de ms) |
| **Mobile** | Flutter | App participante cross-platform |
| **Frontend Web** | React + Tailwind + Vite | Dashboard do gestor |
| **Document DB** | MongoDB (opcional) | Dados não-estruturados de documentos, contratos |
| **Auth** | OAuth 2.0 + OpenID Connect + WebAuthn/passkeys | Passwordless-first |
| **Deploy** | Kubernetes (Digital Ocean / AWS) | Multi-região para disaster recovery |
| **CI/CD** | GitHub Actions + ArgoCD | GitOps com deploy contínuo |
| **Infra as Code** | Terraform + Pulumi | Toda infraestrutura versionada |

### 4.1. Padrões Arquiteturais

| Padrão | Onde |
|--------|------|
| **Event Sourcing** | Todas as transações financeiras (stream imutável) |
| **CQRS** | Separação total entre comandos e queries |
| **Saga Coreográfica** | Workflows longos (onboarding de 7 passos, fechamento contábil) |
| **API Gateway** | BFF separado para web, mobile e parceiros |
| **Strangler (inbound)** | Não vamos migrar dados de legados — cada cliente começa do zero ou importa saldo inicial |
| **Feature Flags** | Liberação incremental para tenants pilotos |
| **Canary Deploy** | Novo código roda para 1% dos tenants antes de 100% |
| **Chaos Engineering** | Testes de resiliência em produção (fora de horário comercial) |

---

## 5. Modelo de Dados (Zero Legacy)

Não existem tabelas `FAVOR`, `LANCONT`, `NATFIN`, `SEQ_FAVORECIDO`, `@Alias("CENCUST")`. Nosso modelo é:

```
events (event store — imutável)
├── stream_id (aggregate root)
├── event_type (transaction.created, member.onboarded, etc.)
├── event_data (JSON)
├── event_metadata (trace_id, user_id, tenant_id)
├── version (controle de concorrência otimista)
└── created_at

materialized_views (CQRS — atualizados por projeções)
├── member_current_state
├── fund_current_state
├── transaction_summary (por período, tipo, fundo)
├── daily_balances
├── payment_order_status
└── reconciliation_status

analytics (ClickHouse)
├── member_events (cada interação do participante)
├── transaction_analytics (por dimensão)
├── cost_benchmarks (anônimo, cross-tenant)
└── fraud_scores (histórico para treino de modelo)
```

---

## 6. Precificação (Disruptiva)

Nada de "1% do patrimônio" como os legados.

| Tier | Preço | Público | Funcionalidades |
|------|-------|---------|-----------------|
| **Starter** | R$ 0 (freemium) | Fundos < R$ 50M | Cadastro, transações manuais, dashboard básico |
| **Growth** | R$ 2.000 + R$ 0,30/participante ativo | Fundos R$ 50M-R$ 1B | API, automação de remessas, conciliação básica, app participante |
| **Scale** | R$ 5.000 + R$ 0,50/participante ativo | Fundos R$ 1B-R$ 5B | ML antifraude, fechamento automático, governance hub, BI |
| **Enterprise** | R$ 15.000 + R$ 0,80/participante ativo | Fundos > R$ 5B | Open Finance, marketplace, regulation radar, SLA 2h, nuvem privada |

**Diferencial de entrada:** Starter gratuito para fundos pequenos — cria dependência e base de referência. Quando crescerem, migram naturalmente para Growth/Scale.

```
Exemplo de conta Scale (3.000 participantes):
  R$ 5.000 + 3.000 × R$ 0,50 = R$ 6.500/mês
  → ~50% mais barato que o concorrente mais próximo
  → + portal do participante (que nenhum concorrente oferece)
  → + API pública para integrações
```

---

## 7. Roadmap de Entrada no Mercado

### Fase 0 — Fundação (Meses 1-4)

**Time:** 5 pessoas (1 PM/domain expert, 2 TS/React, 1 Rust, 1 infra)

| Entrega | Descrição |
|---------|-----------|
| Event Store + motor de transações imutáveis | Core do sistema em Rust |
| GraphQL API para `members` + `transactions` | CRUD básico + event stream |
| Protótipo do app mobile (Flutter) | Consulta de saldo, extrato |
| Tenant provisionamento manual | Multi-tenancy via database-per-tenant |
| Integração PIX (primeiro banco) | Pagamentos via PIX |

**Validação de mercado:** 3 fundos pilotos usando o Starter gratuito.

### Fase 1 — Product-Market Fit (Meses 5-10)

**Time:** 12 pessoas (+2 TS, +1 Rust, +1 Flutter, +1 ML, +1 CS, +1 designer)

| Entrega | Descrição |
|---------|-----------|
| Conciliação contínua (tempo real) | Stream de conciliação com matching automático |
| Onboarding digital (selfie + biometria) | Participante cria conta em 5 min pelo celular |
| ML antifraude básico | Score de risco em pagamentos |
| Dashboard do gestor | Web React com KPIs em tempo real |
| Ciclo contábil automático | Journal rules derivadas do type da transaction |
| API pública v1 | Documentação, rate limits, webhooks |

**Clientes:** 10 fundos pagantes (Growth). MRR: ~R$ 50k.

### Fase 2 — Escala (Meses 11-18)

**Time:** 25 pessoas

| Entrega | Descrição |
|---------|-----------|
| Governance Hub | Board management, comitês, votações |
| Regulation Radar | Monitoramento automático de mudanças PREVIC/Receita |
| Cashflow Predictor | ML de previsão de fluxo de caixa |
| Anomaly Detector Cross-tenant | ML que aprende padrões entre todos os fundos |
| Marketplaces de parceiros | Asset managers, auditorias, atuárias |
| Integração Open Finance | Iniciação de pagamento, compartilhamento de dados |
| Gamificação | Engajamento de participantes com metas e selos |

**Clientes:** 40 fundos pagantes (Growth + Scale). MRR: ~R$ 300k.

### Fase 3 — Plataforma (Meses 19-24)

**Time:** 40+ pessoas

| Entrega | Descrição |
|---------|-----------|
| SDK público | Terceiros constroem na plataforma |
| White label | Outras empresas revendem com marca própria |
| Expansão EAPC + planos de saúde | Mercados adjacentes |
| App Android/iOS nativo | Performance e recursos do dispositivo |
| Certificação ISO 27001 | Compliance para enterprise |
| Nuvem privada para clientes grandes | Cluster dedicado por tenant |

**Clientes:** 100+ fundos. MRR: ~R$ 1,2M. **ARR: ~R$ 15M.**

---

## 8. Go-to-Market (Como Vender)

Não vamos vender como os incumbentes (consultoria cara, ciclo de vendas de 12 meses).

### 8.1. Canais

| Canal | Estratégia | Custo |
|-------|-----------|-------|
| **Inbound** | Conteúdo sobre "modernização de fundos de pensão", "Open Finance para EFPCs", "custo administrativo" | Baixo |
| **Parceria com atuárias** | Atuárias indicam o sistema para fundos que atendem | Comissão 15% |
| **Parceria com auditores** | Auditores veem a dor dos sistemas legados nos clientes | Comissão 10% |
| **Direct sales** | Venda consultiva para fundos médios (R$ 1-5B) | 2 vendedores |
| **Product-led growth** | Starter gratuito → auto-onboarding → conversão paga | Zero (produto vende sozinho) |
| **Eventos ABRAPP/ICSS** | Presença em congressos do setor de previdência | Alto, mas necessário |

### 8.2. Narrative de Venda

```
"O senhor sabia que seus participantes nunca acessaram o sistema atual?
E que 40% dos pedidos de informação que chegam na tesouraria são
'qual meu saldo?' ou 'mudança de conta bancária'?

Com o ClearPension, o participante vê o saldo no celular em tempo real,
atualiza os próprios dados, e o senhor reduz em 60% as solicitações
internas. Sem custo de implantação. Em 30 dias está rodando.

E o melhor: o sistema aprende padrões de fraude, prevê fluxo de caixa
e atualiza automaticamente as obrigações fiscais. Coisa que sistema
nenhum faz hoje."
```

---

## 9. Riscos e Por Que Vamos Vencer

### 9.1. Riscos

| Risco | Mitigação |
|-------|-----------|
| **Fundos são conservadores e não trocam de sistema** | Entrar por fundos pequenos/médios (crise maior, mais abertos a mudança); Starter gratuito reduz barreira |
| **Regulamentação muda e exige adaptação** | Regulation radar + regras versionadas: adaptação em dias, não meses |
| **Concorrente copia nossa abordagem** | Rede de participantes + marketplace = barreira de saída; levaria 2-3 anos para um concorrente copiar |
| **Dados sensíveis geram desconfiança** | ISO 27001, criptografia, database-per-tenant, nuvem privada opcional |
| **Custo de aquisição alto** | PLG + parcerias reduzem CAC; freemium gera demanda orgânica |
| **Time não conhece o domínio** | Contratar 1 domain expert de previdência nos primeiros 3 meses |

### 9.2. Vantagens Competitivas

1. **App participante mobile** — nenhum concorrente tem. É o motivo #1 de troca de sistema.
2. **Preço baseado em participante, não em % do patrimônio** — escala natural conforme o fundo cresce, sem susto na conta.
3. **API-first** — integração com RH, bancos, Open Finance, custodiantes. O sistema legado nem tem REST API.
4. **IA desde o dia 1** — detecção de fraudes, previsão de fluxo, regulação. O concorrente não tem ML.
5. **Governance Hub** — um mercado adjacente inteiro (board management, comitês) que ninguém ataca.
6. **Event sourcing** — auditoria nativa, rollback para qualquer ponto no tempo, saldo recalculável.
7. **Multi-tenant com learning cross-tenant** — cada fundo aprende com os padrões de todos os outros (anônimo). O monolito legado não tem essa visão.

---

## 10. Resumo: ClearPension

```
PRODUTO:      ClearPension — Plataforma moderna de gestão financeira para fundos de pensão

DIFERENCIAL:  Mobile-first, API-pública, IA embarcada, governance hub, Open Finance

CLIENTE:      EFPCs pequenas/médias insatisfeitas com sistemas legados

ENTRADA:      Starter gratuito → conversão paga → expansão para governance + marketplace

MODELO:       R$ 0 / R$ 2k+R$0,30/part / R$ 5k+R$0,50/part / R$ 15k+R$0,80/part

DOMÍNIOS:     members (não favorecido), funds (não planos), transactions (imutáveis, event-sourced),
              payment-orders, reconciliation-stream, participant-engagement, governance-hub,
              intelligence-layer, ecosystem-marketplace, open-finance-hub, cost-intelligence

STACK:        Rust (core) + TypeScript (API) + Flutter (mobile) + React (web) + EventStoreDB
              + Kafka + ClickHouse + PostgreSQL + ONNX Runtime (ML)

STARTER GRATUITO → fundos pequenos crescem conosco
APP PARTICIPANTE → o que o concorrente não tem
IA EMBARCADA    → antifraude, previsão, regulação
API PÚBLICA     → ecossistema de parceiros

RECEITA:
  Ano 1: R$ 500k ARR (10 fundos)
  Ano 2: R$ 4M ARR (40 fundos)
  Ano 3: R$ 15M ARR (100+ fundos)

Não estamos reescrevendo um legado.
Estamos construindo o que o legado nunca será.
```

---

*Documento gerado em 2026-06-22*
*ClearPension — concorrente nativo digital para o mercado de fundos de pensão*
