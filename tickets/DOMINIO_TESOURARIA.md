# Domínio de Negócio — dataa-tesouraria

## Mapeamento Completo do Domínio de Tesouraria de Fundos de Pensão

---

## 1. O Negócio: Gestão de Tesouraria de Fundos de Pensão

O **dataa-tesouraria** é um sistema de gestão financeira e contábil para **Entidades Fechadas de Previdência Complementar (EFPC)** — popularmente conhecidas como **fundos de pensão**. Estas entidades administram os recursos de participantes (empregados de uma ou mais empresas) que contribuem durante a vida laboral para formar uma reserva que será paga como benefício de aposentadoria.

O sistema cobre o ciclo completo: desde o cadastro de participantes e planos, passando pela arrecadação de contribuições, investimento dos recursos, pagamento de benefícios, contabilidade, reconciliação bancária, até a geração de obrigações fiscais e acessórias (EFD, REINF, PIS/COFINS).

---

## 2. Conceitos Fundamentais do Domínio

### 2.1. Plano de Benefícios

Núcleo do negócio. Um **plano de benefícios** define as regras de um fundo de pensão específico:

- **Plano CD (Contribuição Definida)**: cada participante tem uma conta individual; o benefício depende do saldo acumulado
- **Plano BD (Benefício Definido)**: o benefício é conhecido antecipadamente; as contribuições são calculadas para garantir o pagamento
- **Plano CV (Contribuição Variável)**: híbrido, combina elementos de CD e BD

Cada plano possui:
- **Participantes** (empregados ativos, assistidos/aposentados, pensionistas)
- **Patrocinadores** (empresas que patrocinam o plano) e **Instituidores** (sindicatos, associações)
- **Regras de custeio** (percentuais de contribuição)
- **Perfis de investimento** (alocação de recursos)
- **Convênios bancários** (contas específicas para movimentação)

### 2.2. Favorecido (Participante, Patrocinador, Fornecedor)

Entidade central que representa **qualquer pessoa física ou jurídica** que se relaciona financeiramente com o fundo:

| Subtipo | Descrição |
|---------|-----------|
| **Participante** | Empregado ou associado que contribui para o plano |
| **Patrocinador** | Empresa que patrocina o plano e contribui |
| **Instituidor** | Sindicato/associação que instituiu o plano |
| **Fornecedor** | Prestador de serviço (médico, advogado, etc.) |
| **Prestador** | Qualquer entidade que recebe pagamento |

Cada favorecido possui dados cadastrais (CPF/CNPJ, dados bancários para pagamento, endereço, contatos) e pode estar associado a múltiplos planos.

### 2.3. Lançamento (Movimento Financeiro)

Registro individual de **entrada ou saída de recursos**. É a unidade atômica da tesouraria:

- **Lançamento Simples**: entrada ou saída isolada
- **Lançamento Contábil**: com partidas dobradas (débito/crédito)
- **Baixa de Lançamento**: marca um lançamento como pago/realizado
- **Baixa Parcial**: pagamento fracionado de um lançamento
- **Estorno/Reversão**: cancela um lançamento anterior

Cada lançamento possui: valor, data, natureza financeira, centro de custo, conta contábil, favorecido, histórico, lote contábil.

### 2.4. Remessa (Ordem de Pagamento)

Agrupamento de lançamentos para **envio ao banco para execução financeira**:

- **Remessa**: arquivo enviado ao banco contendo ordens de pagamento
- **Retorno**: arquivo recebido do banco com a confirmação de processamento
- **Cancelamento de Remessa**: solicitação de cancelamento de uma remessa já enviada
- **Controle de Envio**: gestão do ciclo de vida (enviado, processado, confirmado)

### 2.5. Conciliação Bancária

Processo de **confrontação entre os registros do sistema e os extratos bancários**:

- **Importação OFX**: leitura de extratos bancários no formato OFX
- **Movimento Bancário**: registros de movimentação vindos do banco
- **Fitid (Fita de Identificação)**: processo de casamento automático entre lançamentos internos e movimentos bancários
- **Saldo Inicial**: saldo de abertura para conciliação
- **Rastreamento de Movimento Bancário**: trilha de auditoria sobre cada item conciliado

### 2.6. Contabilidade

O módulo mais complexo do sistema (789 classes, 20 subdomínios), responsável por toda a **escrituração contábil** do fundo:

- **Fato Gerador**: evento que origina um registro contábil. É parametrizável: cada combinação de lote + histórico define um fato gerador. Pode ter eventos contábeis, naturezas financeiras e retenções associadas.
- **Lote Contábil**: agrupamento de lançamentos contábeis de um mesmo fato gerador
- **Histórico Padrão**: texto padronizado usado na descrição de lançamentos contábeis. Pode ser parametrizado por plano.
- **Disponível (Disponibilidade)**: registro do **quanto de recurso está disponível** para movimentação em cada plano, por natureza financeira. É um saldo contábil que reflete o que pode ser gasto.
- **Fechamento Contábil**: processo de encerramento do período contábil (mensal), com validação de partidas dobradas, cálculo de resultado e geração de demonstrações
- **Fechamento Contábil Consolidado**: consolidação dos fechamentos de todos os planos em uma visão contábil única da entidade
- **Balancete**: relatório contábil que mostra saldos de contas em um período
- **Razão**: detalhamento das movimentações de cada conta contábil
- **Diário**: livro diário contábil
- **Plano de Contas (Planificação)**: estrutura hierárquica de contas contábeis

### 2.7. Conta Contábil e Natureza Financeira

- **Conta Contábil**: classificação contábil segundo o plano de contas (Ativo, Passivo, Receita, Despesa)
- **Natureza Financeira**: classifica o tipo de movimentação financeira (contribuição, benefício, taxa administrativa, etc.)
- **Conta Contábil para Cálculo de Cota**: conta específica usada no cálculo do valor da cota dos planos CD

### 2.8. Custeio

Define **como os planos são financiados**:

- **Base de Custeio**: alíquotas e valores de contribuição
- **Custeio Administrativo**: taxa de administração do plano
- **Custeio PGA (Plano de Gestão Administrativa)**: custeio específico da gestão administrativa
- **Rateio**: distribuição de custos entre planos

### 2.9. Investimentos e Cotas

Gestão dos **investimentos dos recursos** dos planos:

- **Cota**: unidade de valor dos planos CD. O saldo do participante é expresso em cotas. O valor da cota é recalculado periodicamente.
- **Perfil de Investimento**: define a estratégia de alocação (conservador, moderado, agressivo)
- **Aplicação**: aporte de recursos em um perfil de investimento
- **Resgate**: retirada de recursos de um perfil de investimento
- **Histórico de Cota**: série histórica do valor da cota ao longo do tempo
- **Memória de Cálculo de Histórico de Cota**: detalhamento do cálculo do valor da cota
- **Posição Atual de Histórico de Cota**: snapshot da última posição calculada

### 2.10. Fechamento Financeiro

Processo de **encerramento financeiro do período**, distinto do fechamento contábil:

- **Controle de Envio**: rastreamento do status de envio dos fechamentos
- **Executor**: orquestrador que coordena as etapas do fechamento financeiro

### 2.11. Integração Bancária (Banco do Brasil)

Integração direta com o **Banco do Brasil** para execução de operações financeiras:

| Operação | Descrição |
|----------|-----------|
| **Transferência** | TED/DOC entre contas |
| **Boleto** | Geração e registro de boletos de cobrança |
| **DARF** | Pagamento de tributos federais (Receita Federal) |
| **GPS** | Pagamento de guias da Previdência Social (INSS) |
| **PIX** | Transferências via PIX |

### 2.12. Obrigações Fiscais e Acessórias

- **EFD (Escrituração Fiscal Digital)**: geração do arquivo digital para a Receita Federal
- **REINF (Escrituração Fiscal Digital de Retenções e Informações da Contribuição Previdenciária)**: informação de retenções na fonte
- **PIS/COFINS**: cálculo e apuração das contribuições
- **Retenção**: impostos retidos na fonte (IR, CSLL, PIS, COFINS, INSS) sobre pagamentos a fornecedores. Códigos de retenção parametrizáveis.
- **Código REINF**: parametrização de códigos para a escrituração REINF

### 2.13. Estrutura Organizacional

- **Centro de Custo**: departamento ou área da entidade. Usado para rateio de despesas e alocação de lançamentos.
- **Departamento**: unidade organizacional
- **Agência**: agência bancária
- **Instituição Financeira**: banco ou instituição financeira (com código COMPE)

### 2.14. Processos e Workflows

- **Processo**: entidade que representa um processo administrativo (com numeração sequencial)
- **Parâmetro de Processo**: configurações associadas a processos específicos

### 2.15. Segurança e Auditoria

- **Trilha de Auditoria**: log de todas as alterações em dados sensíveis
- **Log de Erros**: registro centralizado de erros de processo
- **Log de Carga**: log de processos de importação de dados

---

## 3. Macro-Processos de Negócio

### 3.1. Ciclo de Arrecadação (Entradas)

```
Contribuição Participante → Lançamento de Entrada → Remessa ao Banco → Conciliação → Contabilização
```

1. Folha de contribuição é processada (contribuição do participante + patrocinador)
2. Lançamentos de entrada são gerados no plano
3. Recursos são enviados ao banco via remessa (ou recebidos automaticamente)
4. Extrato bancário é importado e conciliado
5. Partidas contábeis são geradas automaticamente pelos fatos geradores

### 3.2. Ciclo de Pagamentos (Saídas)

```
Benefício Aposentadoria → Lançamento de Saída → Remessa ao Banco → Pagamento → Conciliação
```

1. Benefícios a pagar são calculados (aposentadorias, pensões)
2. Lançamentos de saída (débito) são gerados
3. Remessa bancária é montada e enviada ao Banco do Brasil
4. Banco processa os pagamentos e envia arquivo de retorno
5. Baixa automática nos lançamentos é realizada pela conciliação

### 3.3. Ciclo de Fechamento Contábil (Periódico)

```
Fatos Geradores → Lançamentos Contábeis → Fechamento Diário → Fechamento Mensal → Demonstrações → Consolidação
```

1. Lançamentos financeiros geram fatos geradores contábeis automaticamente
2. Lançamentos contábeis são agrupados em lotes por plano
3. Fechamento diário valida as partidas do dia
4. Fechamento mensal encerra o período contábil
5. Demonstrações contábeis são geradas (balancete, razão, diário)
6. Consolidação contábil agrupa todos os planos

### 3.4. Ciclo de Investimentos

```
Aplicação → Cálculo de Cota → Resgate → Posição
```

1. Recursos não utilizados são aplicados conforme perfil de investimento
2. Valor da cota é recalculado periodicamente com base na rentabilidade
3. Resgates são processados conforme necessidade de caixa
4. Posição de investimentos é monitorada continuamente

---

## 4. Entidades-Chave e Relacionamentos

```
Plano
  ├── Favorecidos (Participantes, Patrocinadores, Instituidores)
  ├── Custeio (regras de contribuição)
  ├── Perfis de Investimento → Aplicações / Resgates
  ├── Contas Contábeis para Cálculo de Cota
  ├── Convênios Bancários
  └── Lançamentos
        ├── Histórico (descrição padronizada)
        ├── Natureza Financeira
        ├── Centro de Custo
        ├── Retenções Fiscais
        └── Lote Contábil

Lote Contábil
  └── Fato Gerador
        ├── Evento Contábil
        ├── Natureza Financeira associada
        └── Retenções associadas

Remessa Bancária
  ├── Lançamentos associados
  └── Conciliação Bancária (via Fitid)

Conciliação
  ├── Movimento Bancário (importado)
  └── Saldo Inicial
```

---

## 5. Mapa de Subdomínios por Complexidade

### 5.1. Core Domain (Diferenciação Competitiva)

| Subdomínio | Complexidade | Descrição |
|------------|-------------|-----------|
| Fechamento Contábil | Muito Alta | Lógica de encerramento contábil com validação, cálculo de resultado, encerramento de exercício, reabertura. É o coração do sistema. |
| Cálculo de Cota | Muito Alta | Cálculo do valor da cota para planos CD, com memória de cálculo detalhada e posição atual. Exige precisão absoluta. |
| Fato Gerador | Alta | Motor de parametrização contábil que mapeia eventos financeiros em partidas contábeis. É onde a inteligência contábil do sistema reside. |
| Conciliação Bancária (Fitid) | Alta | Algoritmo de casamento automático entre lançamentos internos e extratos bancários. Exige fuzzy matching e tratamento de exceções. |

### 5.2. Supporting Domain (Apoio)

| Subdomínio | Complexidade | Descrição |
|------------|-------------|-----------|
| Cadastro de Favorecidos | Média-Alta | Gestão de múltiplos tipos de favorecido com vínculos complexos (participante em múltiplos planos, patrocinadores) |
| Gestão de Planos | Média | Cadastro e configuração de planos de benefício |
| Remessa Bancária | Média | Geração de arquivos de remessa e interpretação de retorno |
| Custeio | Média | Cálculo de contribuições e rateios |
| Importação de Arquivos | Média | Importação de folhas, extratos OFX, arquivos de retorno bancário |

### 5.3. Generic Subdomain (Comoditizado)

| Subdomínio | Complexidade | Descrição |
|------------|-------------|-----------|
| CEP | Baixa | Consulta de endereços por CEP |
| Feriados | Baixa | Calendário de feriados |
| Exportação (CSV, XLS, PDF) | Baixa | Geração de relatórios em formatos variados |
| Integração com Banco do Brasil | Média | APIs bancárias (boletos, DARF, GPS, TED) — embora crítica, é uma integração padrão |

---

## 6. Sugestões de Melhorias de Negócio e Modelo

> Estas sugestões são **puramente de negócio/domínio**, sem envolver tecnologia ou código.

### 6.1. Motor de Regras de Custeio Configurável pelo Negócio

**Problema atual:** As regras de custeio (alíquotas, bases de cálculo, rateios) estão embutidas no código ou em parametrizações complexas que exigem TI para alterar.

**Sugestão:** Criar um **motor de regras de custeio** que permita ao atuário ou analista de previdência configurar diretamente:
- Fórmulas de contribuição (ex: "salário real acima do teto do INSS × alíquota de 7,5%")
- Regras de rateio administrativo entre planos
- Cenários de simulação atuarial
- Regras de transição entre faixas salariais

**Benefício:** Redução do tempo de implementação de novos planos de dias para horas. O negócio ajusta sem depender de sprint de TI.

### 6.2. Workflow de Aprovação de Pagamentos

**Problema atual:** Lançamentos e remessas são criados e enviados sem um fluxo hierárquico de aprovação.

**Sugestão:** Implementar um **workflow de aprovação** com:
- Regras de alçada (valores baixos aprovados por analista, altos por comitê)
- Múltiplas assinaturas para pagamentos acima do teto
- Trilha de auditoria de quem aprovou cada etapa
- Notificações para aprovadores quando há pagamentos pendentes

**Benefício:** Redução de risco operacional e conformidade com controles internos (SOX, COSO). Atende exigências de auditoria de fundos de pensão.

### 6.3. Gestão de Liquidez e Fluxo de Caixa Projetado

**Problema atual:** O sistema gerencia o disponível (quanto tem) mas não projeta cenários futuros de caixa.

**Sugestão:** Adicionar um **módulo de gestão de liquidez** com:
- Projeção de fluxo de caixa baseada em obrigações futuras conhecidas (benefícios a pagar, contribuições esperadas)
- Cenários "what-if" (ex: "se 20% dos participantes migrarem para perfil conservador")
- Alertas de descasamento de curto prazo (obrigações vs. disponível)
- Recomendação de aplicação/resgate com base na necessidade projetada

**Benefício:** Otimização da rentabilidade ao evitar recursos parados ou resgates emergenciais. O gestor do fundo toma decisões baseado em projeções, não apenas no saldo atual.

### 6.4. Automação de Conciliação com Aprendizado de Padrões

**Problema atual:** A conciliação (Fitid) exige configuração manual de regras de casamento e ainda gera exceções que precisam de resolução manual.

**Sugestão:** Sistema de conciliação que **aprende padrões**:
- Historicamente, identifica automaticamente novos padrões de correspondência
- Sugere regras de conciliação baseadas em casamentos manuais anteriores
- Agrupa exceções por tipo para resolução em lote
- Dashboard de "saúde da conciliação" com indicadores de automaticidade

**Benefício:** Redução de horas de conciliação manual. Quanto mais o sistema é usado, menos exceções manuais são geradas.

### 6.5. Portal do Participante com Autosserviço

**Problema atual:** Participantes dependem da equipe interna para consultar saldo, extrato, contribuições.

**Sugestão:** **Portal de autosserviço** onde o participante pode:
- Consultar saldo de conta (em cotas e em valor)
- Ver extrato de contribuições e benefícios
- Simular benefício futuro
- Atualizar dados bancários
- Solicitar portabilidade entre perfis de investimento
- Acompanhar solicitações em andamento

**Benefício:** Redução de carga operacional da equipe interna. Aumento de transparência para o participante. Diferencial competitivo na retenção de planos.

### 6.6. Gestão de Riscos Fiscais em Tempo Real

**Problema atual:** Retenções fiscais (IR, PIS, COFINS, CSLL, INSS) são calculadas no momento do pagamento e conferidas manualmente.

**Sugestão:** Módulo de **compliance fiscal em tempo real**:
- Validação de alíquotas contra tabelas vigentes antes de cada pagamento
- Alertas de retenção incorreta antes do envio ao banco
- Cruzamento automático com obrigações acessórias (EFD, REINF)
- Dashboard de exposição fiscal por plano/período

**Benefício:** Prevenção de multas por retenção incorreta ou fora do prazo. Redução de retrabalho em obrigações acessórias.

### 6.7. Orquestração de Ciclo Contábil Automatizada

**Problema atual:** O fechamento contábil exige acompanhamento manual de múltiplas etapas (validação, rateio, encerramento, consolidação).

**Sugestão:** **Orquestrador inteligente de ciclo contábil**:
- Pipeline autoexecutável: fatos geradores → contabilização → rateio → fechamento diário → fechamento mensal → consolidação
- Pontos de verificação com aprovação opcional (ex: "aprovado pelo contador antes de consolidar")
- Recuperação automática de falhas (se uma etapa falha, o pipeline pausa e notifica)
- SLA auditável (abertura em X dias, fechamento em Y dias)

**Benefício:** Previsibilidade no ciclo contábil. Redução de atrasos no fechamento mensal. Auditoria clara sobre prazos.

### 6.8. Gestão de Convênios Bancários Centralizada

**Problema atual:** Cada convênio bancário (conta corrente, conta investimento) é cadastrado e gerenciado dentro do plano, sem visão consolidada.

**Sugestão:** **Central de Convênios** com:
- Catálogo único de todas as contas bancárias da entidade
- Mapeamento de quais contas servem quais planos
- Gestão de limites e tarifas bancárias por convênio
- Alertas de saldo baixo em contas operacionais
- Relatório de custo bancário por plano/período

**Benefício:** Negociação mais eficiente com bancos (visão consolidada de tarifas). Redução de contas sem movimentação.

### 6.9. Precificação de Planos por Margem

**Problema atual:** A taxa de administração (custeio administrativo) é definida no desenho do plano e raramente revista.

**Sugestão:** Módulo de **análise de margem por plano**:
- Cálculo automático do custo real de administração por plano (horas de equipe, sistemas, infraestrutura)
- Comparação com a receita de taxa administrativa
- Recomendação de reajuste com base em custo real + inflação
- Simulação de impacto de reajuste nos participantes

**Benefício:** Identificação de planos deficitários. Precificação baseada em dados, não em achismo. Sustentabilidade financeira dos planos.

### 6.10. Conciliação de Investimentos com Administradores

**Problema atual:** Posições de investimento (cotas de fundos, títulos públicos) são informadas por administradores externos e conferidas manualmente.

**Sugestão:** **Conciliação automatizada de posições**:
- Importação automática de posições de todos os administradores (custodiante, gestores)
- Cálculo da posição esperada vs. informada
- Detecção de divergências com abertura automática de chamado
- Valorização da carteira consolidada em tempo real

**Benefício:** Precisão na posição dos investimentos. Detecção rápida de erros de administradores. Base confiável para o cálculo da cota.

### 6.11. Simulação Atuarial Integrada

**Problema atual:** Estudos atuariais são feitos fora do sistema, em planilhas ou softwares especializados, sem integração com dados reais.

**Sugestão:** Módulo de **simulação atuarial integrada**:
- Massa de dados real (participantes, contribuições, benefícios) disponível para simulação
- Hipóteses ajustáveis (taxa de juros, tábua de mortalidade, rotatividade)
- Cálculo do plano de custeio recomendado
- Relatório de adequação da reserva matemática

**Benefício:** Atuários trabalham com dados reais do sistema. Redução de inconsistências entre sistemas. Agilidade na definição do custeio anual.

### 6.12. Gestão de Documentos e Processos

**Problema atual:** Documentos relacionados a pagamentos (notas fiscais, contratos, comprovantes) ficam em sistemas separados ou arquivo físico.

**Sugestão:** **Digital Asset Management integrado**:
- Anexo de documentos digitais a lançamentos e processos
- OCR para extração automática de dados de notas fiscais e boletos
- Workflow de aprovação documental vinculado ao pagamento
- Repositório auditável com retenção por prazo legal
- Assinatura digital integrada

**Benefício:** Eliminação de papel. Conformidade com prazos legais de guarda de documentos. Redução de retrabalho ("cadê a nota fiscal deste pagamento?").

---

## 7. Proposta de Microsserviços por Contexto Delimitado

### 7.1. Contextos Delimitados (Bounded Contexts)

Abaixo, a divisão do monolito em contextos que podem evoluir independentemente como microsserviços, organizados por prioridade de extração:

### Nível 1 — Extração Imediata (Baixo Acoplamento, Alto Ganho)

| Microserviço | Responsabilidade | API Pública |
|-------------|-----------------|-------------|
| **cadastro-favorecido** | CRUD completo de favorecidos (participantes, patrocinadores, instituidores, fornecedores), validação de CPF/CNPJ, dados bancários, endereço, contatos | `POST /favorecidos`, `GET /favorecidos/{id}`, `GET /favorecidos?documento=...` |
| **gestao-planos** | Cadastro e configuração de planos de benefício, associação de favorecidos a planos, regras do plano | `POST /planos`, `GET /planos/{id}`, `POST /planos/{id}/vinculos` |
| **instituicao-financeira** | Catálogo de bancos, agências, convênios bancários, contas | `GET /bancos`, `GET /agencias`, `POST /convenios`, `GET /convenios/{id}/saldo` |

### Nível 2 — Domínio Core (Extrair com Cautela)

| Microserviço | Responsabilidade | API Pública |
|-------------|-----------------|-------------|
| **contabilidade** | Fato gerador, lotes contábeis, lançamentos contábeis, fechamento, balancete, razão, diário, consolidação | `POST /fatos-geradores/processar`, `POST /lotes`, `POST /fechamento/mensal`, `GET /balancete` |
| **tesouraria-operacoes** | Lançamentos financeiros, remessas, conciliação, baixas, estornos | `POST /lancamentos`, `POST /remessas`, `POST /conciliacao/fitid`, `POST /lancamentos/{id}/baixa` |
| **investimentos-cotas** | Perfis de investimento, aplicação/resgate, cálculo de cota, posição | `POST /aplicacoes`, `POST /resgates`, `POST /calculo-cota`, `GET /posicao/{planoId}` |
| **custeio** | Regras de custeio, rateio, cálculo de contribuições, PGA | `POST /calcular-contribuicoes`, `POST /rateio`, `GET /custeio/{planoId}` |

### Nível 3 — Integração e Fiscal

| Microserviço | Responsabilidade | API Pública |
|-------------|-----------------|-------------|
| **integracao-bancaria** | Conexão com Banco do Brasil (transferências, boletos, DARF, GPS, PIX) | `POST /transferencias`, `POST /boletos`, `POST /darf`, `POST /gps` |
| **obrigacoes-fiscais** | EFD, REINF, PIS/COFINS, retenções, parametrização de códigos | `POST /gerar-efd`, `POST /gerar-reinf`, `GET /retencoes/calcular` |
| **conciliacao-bancaria** | Motor de conciliação (Fitid), importação OFX, rastreamento, exceções | `POST /importar-ofx`, `POST /conciliar`, `GET /excecoes`, `POST /resolver-excecao` |

### Nível 4 — Infraestrutura e Suporte

| Microserviço | Responsabilidade | API Pública |
|-------------|-----------------|-------------|
| **importacao-dados** | Importação de folhas de pagamento, arquivos bancários, cargas em lote | `POST /importar/folha`, `POST /importar/arquivo`, `GET /importacoes/{id}/log` |
| **exportacao-relatorios** | Geração de relatórios (CSV, XLS, PDF), exportação contábil, demonstrações | `POST /exportar/balancete`, `POST /exportar/extrato`, `GET /exportacoes/{id}/download` |
| **gestao-documentos** | Anexo e gestão de documentos digitais, OCR, workflow de aprovação | `POST /documentos`, `GET /documentos/{lancamentoId}`, `POST /documentos/{id}/aprovacao` |
| **auditoria-trilha** | Log de alterações centralizado, consulta de auditoria, retenção legal | `POST /auditoria/consultar`, `GET /auditoria/entidade/{tipo}/{id}` |
| **notificacoes** | Notificações por e-mail, push, whatsapp para workflow de aprovação e alertas | `POST /notificar`, `POST /preferencias` |

### 7.2. Mapa de Dependências Entre Contextos

```
cadastro-favorecido ──┬──→ tesouraria-operacoes
                      ├──→ contabilidade
                      ├──→ custeio
                      └──→ investimentos-cotas

gestao-planos ────────┬──→ custeio
                      ├──→ investimentos-cotas
                      ├──→ tesouraria-operacoes
                      └──→ contabilidade

tesouraria-operacoes ──┬──→ integracao-bancaria
                      ├──→ conciliacao-bancaria
                      └──→ contabilidade

contabilidade ─────────→ obrigacoes-fiscais

investimentos-cotas ──→ conciliacao-bancaria (via posições)
```

### 7.3. Estratégia de Extração Recomendada

**Fase 1 — Foundation (3 meses):**
Extrair `cadastro-favorecido`, `gestao-planos`, `instituicao-financeira` como serviços independentes. Estes têm baixo acoplamento e trarão ganho imediato (equipes paralelas).

**Fase 2 — Core Financeiro (4 meses):**
Extrair `tesouraria-operacoes` + `conciliacao-bancaria` + `integracao-bancaria`. Estes são os serviços que mais se beneficiam de escalabilidade independente (picos de processamento de remessas).

**Fase 3 — Contábil (4 meses):**
Extrair `contabilidade`. É o mais complexo devido ao fechamento contábil e fatos geradores. Exige mais cuidado com consistência eventual e transações distribuídas.

**Fase 4 — Complementares (2 meses):**
Extrair `investimentos-cotas`, `custeio`, `obrigacoes-fiscais`, `importacao-dados`, `exportacao-relatorios`, `gestao-documentos`, `auditoria-trilha`, `notificacoes`.

### 7.4. Padrão de Comunicação Entre Serviços

- **Eventos de Domínio**: serviços publicam eventos (ex: `LancamentoCriado`, `RemessaEnviada`, `ConciliaçãoRealizada`) via message broker. Serviços interessados consomem assincronamente.
- **API REST Síncrona**: consultas pontuais (ex: `contabilidade` consulta dados do favorecido via API do `cadastro-favorecido`)
- **API Queries Dedicadas**: para evitar acoplamento, cada serviço pode ter uma API de query separada da API de comando (CQRS leve)

---

## 8. Glossário do Domínio

| Termo | Significado |
|-------|------------|
| **EFPC** | Entidade Fechada de Previdência Complementar (fundo de pensão) |
| **Participante** | Pessoa física vinculada a um plano de benefício |
| **Patrocinador** | Empresa que patrocina o plano de benefício |
| **Instituidor** | Sindicato ou associação que instituiu o plano |
| **Assistido** | Participante que já está recebendo benefício (aposentado) |
| **Pensionista** | Dependente de participante que recebe pensão |
| **Plano CD** | Contribuição Definida — benefício depende do saldo acumulado |
| **Plano BD** | Benefício Definido — benefício é conhecido, contribuição é variável |
| **Plano CV** | Contribuição Variável — híbrido de CD e BD |
| **PGA** | Plano de Gestão Administrativa — plano que custeia a administração |
| **Cota** | Unidade de valor de plano CD. Saldo = número de cotas × valor da cota |
| **Disponível** | Saldo contábil disponível para movimentação em um plano |
| **Fato Gerador** | Evento parametrizado que origina registro contábil |
| **Lote** | Agrupamento de lançamentos contábeis de um mesmo fato gerador |
| **Fitid** | Fita de Identificação — processo de conciliação automática |
| **Remessa** | Arquivo enviado ao banco com ordens de pagamento |
| **Retorno** | Arquivo recebido do banco com confirmação de processamento |
| **Natureza Financeira** | Classificação da movimentação (contribuição, benefício, taxa) |
| **Centro de Custo** | Unidade organizacional para rateio de despesas |
| **EFD** | Escrituração Fiscal Digital — obrigação acessória da Receita Federal |
| **REINF** | Escrituração de Retenções e Informações Previdenciárias |
| **DARF** | Documento de Arrecadação de Receitas Federais |
| **GPS** | Guia da Previdência Social |

---

## 9. Indicadores-Chave de Negócio (KPIs)

| KPI | O que mede | Frequência |
|-----|-----------|------------|
| **Tempo de fechamento contábil** | Dias entre fim do mês e conclusão do fechamento | Mensal |
| **Taxa de automação de conciliação** | % de movimentos bancários conciliados automaticamente | Diário |
| **Giro de contas a pagar** | Tempo médio entre lançamento e pagamento | Mensal |
| **Custo administrativo por participante** | R$/participante/mês | Mensal |
| **Índice de aderência fiscal** | % de pagamentos com retenção correta na primeira tentativa | Mensal |
| **Disponibilidade por plano** | Saldo disponível vs. obrigações de curto prazo | Diário |
| **Rentabilidade por perfil** | Retorno sobre investimento por perfil | Mensal |
| **SLA de fechamento** | % de fechamentos concluídos dentro do prazo regulatório | Mensal |

---

## 10. Estratégia SaaS para o Sistema de Tesouraria

### 10.1. O Mercado de Software para EFPC no Brasil

O mercado brasileiro de fundos de pensão (EFPC) possui cerca de **250-300 entidades** ativas, gerindo aproximadamente **R$ 1,2 trilhão em ativos**. Destas:

- **Grandes** (> R$ 10 bi em ativos): ~15-20 entidades — têm sistemas próprios ou contratam suites caras (Oracle, SAP)
- **Médias** (R$ 1-10 bi): ~60-80 entidades — mercado-alvo ideal para SaaS
- **Pequenas** (< R$ 1 bi): ~150-200 entidades — extremamente sensíveis a preço, alto potencial de conversão

**Concorrentes atuais no mercado brasileiro:**

| Concorrente | Modelo | Força | Fraqueza |
|------------|--------|-------|----------|
| **SIS.SP (Cobra)** | Licenciado / On-premise | Líder de mercado, ampla base instalada | Sistema legado (Clarion/Delphi), difícil integração |
| **OrçaFácil** | Licenciado | Focado em orçamento | Não cobre tesouraria completa |
| **SAP / Oracle** | Licenciado pesado | Cobertura completa | Custo proibitivo para médias/pequenas |
| **Sistemas próprios (in-house)** | Desenvolvido internamente | Sob medida para a entidade | Alto custo de manutenção, sem evolução constante |
| **Planilhas Excel** | "Free" | Zero custo de software | Risco operacional altíssimo, sem controle |

**Ninguém hoje oferece um SaaS moderno, multi-tenant, com atualizações contínuas para EFPCs de pequeno e médio porte.** Esta é a oportunidade.

### 10.2. Modelo de Negócio SaaS Proposto

#### 10.2.1. Segmentação de Clientes

| Segmento | Faixa de ativos | nº de participantes | Preço sugerido (mês) |
|----------|----------------|-------------------|---------------------|
| **Small** | Até R$ 500M | Até 5.000 | R$ 3.000 - 5.000 |
| **Medium** | R$ 500M - R$ 5B | 5.000 - 30.000 | R$ 8.000 - 15.000 |
| **Large** | Acima de R$ 5B | Acima de 30.000 | R$ 20.000 - 40.000 |
| **Enterprise** | Personalizado | Ilimitado | Sob consulta |

#### 10.2.2. Modelo de Precificação

| Componente | Modelo | Descrição |
|------------|--------|-----------|
| **Assinatura base** | Mensal fixo | Acesso ao núcleo do sistema (cadastro, lançamentos, contabilidade básica) |
| **Por participante** | Variável | Taxa por participante ativo no plano (ex: R$ 0,50/part./mês) |
| **Módulos adicionais** | Add-ons | Conciliação bancária, portal do participante, obrigações fiscais, BI |
| **Integrações** | Por conexão | Banco do Brasil, outros bancos, sistemas de RH (ponto extra) |
| **Suporte premium** | Tier | Suporte 24h, SLA 2h, gerente de sucesso dedicado |
| **Implementação** | One-time | Onboarding, migração de dados, treinamento (R$ 10k-50k) |

**Exemplo de receita mensal:**

Uma EFPC média com 12.000 participantes, plano base + módulo de conciliação + portal do participante:
```
Assinatura base:     R$ 8.000
12.000 part. × 0,50: R$ 6.000
Conciliação:         R$ 2.000
Portal participante: R$ 1.500
Total mensal:        R$ 17.500
Anual:               R$ 210.000
```

Com 30 clientes médios em 3 anos: **~R$ 6,3M de receita recorrente anual (ARR).**

#### 10.2.3. Estrutura de Planos

| Funcionalidade | Starter | Business | Enterprise |
|---------------|---------|----------|------------|
| Cadastro de favorecidos | ✓ | ✓ | ✓ |
| Lançamentos financeiros | ✓ | ✓ | ✓ |
| Contabilidade básica | ✓ | ✓ | ✓ |
| Remessa bancária | ✓ | ✓ | ✓ |
| Conciliação bancária | — | ✓ | ✓ |
| Fechamento contábil | — | ✓ | ✓ |
| Obrigações fiscais (EFD/REINF) | — | ✓ | ✓ |
| Portal do participante | — | — | ✓ |
| BI / Dashboards | — | — | ✓ |
| API pública | — | — | ✓ |
| Suporte | E-mail | 8×5 chat | 24×7 dedicado |
| SLA | 48h | 8h | 2h |
| Preço estimado | R$ 3-5k/mês | R$ 8-15k/mês | R$ 20-40k/mês |

### 10.3. Diferenciais Competitivos para um SaaS de EFPC

#### 10.3.1. Compliance como Serviço

O maior pesadelo de uma EFPC pequena/média é manter-se em dia com as obrigações regulatórias. Um SaaS pode **automatizar completamente**:

- **EFD-Reinf**: geração automática mensal, pronta para envio ao governo
- **PIS/COFINS**: cálculo automático por regime (cumulativo/não-cumulativo)
- **Retenções na fonte**: tabelas de alíquotas atualizadas automaticamente pela plataforma
- **Obrigações PREVIC**: relatórios regulatórios para a Superintendência Nacional de Previdência Complementar
- **Auditoria**: trilha completa pronta para apresentar a auditores internos e externos

**Valor percebido:** "Não preciso mais me preocupar com multa por atraso de obrigação acessória. O sistema resolve."

#### 10.3.2. Rede de Benchmarking entre Fundos

Um SaaS multi-tenant pode gerar **inteligência coletiva** que nenhum sistema on-premise consegue:

- **Ranking anônimo de eficiência**: custo administrativo por participante vs. fundos similares
- **Comparativo de rentabilidade**: retorno por perfil de investimento vs. pares
- **Indicadores setoriais**: tempo médio de fechamento, taxa de automação de conciliação
- **Alertas de "fora da curva"**: "Sua entidade está 40% acima da média em custo administrativo para o seu porte"

**Barreira de saída:** O cliente não leva os benchmarks quando sai. O valor da rede só existe dentro da plataforma.

#### 10.3.3. Marketplace de Integrações

| Integração | Descrição |
|-----------|-----------|
| **Banco do Brasil** | Transferências, boletos, DARF, GPS, PIX, extrato |
| **Bradesco / Itaú / Santander** | Mesmas operações para outros bancos |
| **Sistemas de RH** | Folha de pagamento (RM, Senior, Totvs) |
| **Custodiante** | Posição de investimentos (Vórtx, BTG, Itaú) |
| **Governo** | EFD, REINF, DCTFWeb |
| **Bancos digitais** | Contas digitais para maior agilidade |
| **Assinatura digital** | ZapSign, DocuSign, Clicksign |

#### 10.3.4. Modelo "Land and Expand"

Entrada com módulo de maior dor (ex: conciliação bancária ou contabilidade) e expansão para os demais:

```
Land (Mês 1-3):           Expand (Mês 3-6):        Expand (Mês 6-12):
Conciliação Bancária    + Lançamentos             + Contabilidade
                        + Remessas                + Obrigações Fiscais
                        + Cadastro                + Portal Participante
                        → Receita dobra           → Receita triplica
```

### 10.4. Desafios Específicos de um SaaS de EFPC

#### 10.4.1. Personalização vs. Padronização

Cada EFPC tem regras únicas de plano de contas, rateio, custeio, fatos geradores. O SaaS precisa ser **altamente parametrizável sem exigir código**:

- **Plano de contas**: cada entidade tem seu plano de contas próprio, baseado no COSIF mas adaptado. Precisa ser 100% configurável.
- **Fatos geradores**: o mapeamento de eventos financeiros × partidas contábeis é específico de cada entidade. O motor precisa permitir configuração por UI.
- **Rateios**: regras de distribuição de custos entre planos variam enormemente.

**Solução:** O motor de parametrização contábil (fato gerador, rateio, histórico) DEVE ser o primeiro investimento do SaaS. Sem ele, cada cliente vira projeto de consultoria.

#### 10.4.2. Migração de Dados

Cada novo cliente vem de um sistema legado diferente (SIS.SP, Excel, sistema próprio). A migração é o maior risco de churn no onboarding.

**Estratégia:**
- **Conectores de migração** pré-construídos para os 5 sistemas mais comuns
- **Ferramenta de auto-onboarding** que mapeia planilhas Excel para as entidades do sistema
- **Período de paralelismo** (30-60 dias) onde ambos os sistemas rodam simultaneamente
- **Validação automática** de saldos (soma dos lançamentos = saldo contábil esperado)

#### 10.4.3. Segurança e Sigilo Bancário

Dados financeiros de fundos de pensão são **extremamente sensíveis**. Requisitos:

- Isolamento rigoroso entre tenants (fundos diferentes NÃO podem ver dados uns dos outros)
- Criptografia em repouso e em trânsito
- Logs de auditoria imutáveis para toda operação financeira
- Conformidade com LGPD (participantes são titulares de dados pessoais)
- Certificação ISO 27001 como requisito de venda
- Possibilidade de nuvem privada para clientes enterprise

#### 10.4.4. Disponibilidade e Continuidade

Processamento de remessas bancárias e fechamento contábil são **time-sensitive**:
- Remessas precisam ser enviadas até horários de corte bancário (ex: 15h)
- Fechamento contábil tem prazos regulatórios fixos (até dia 15 do mês seguinte)
- Sistema não pode ficar indisponível em dias de fechamento

**Estratégia:**
- SLA de 99.5% mínimo (justificável: ~3,5h de downtime/mês é aceitável para janelas noturnas)
- Janelas de manutenção programadas em horários de baixa atividade (sábados à noite)
- Processamento de remessas com fila de retry e fallback manual
- Modo contingência: possibilidade de gerar arquivos de remessa mesmo com sistema parcialmente indisponível

### 10.5. Roadmap de Produto SaaS

#### Fase 1 — MVP (6 meses)

**Público-alvo:** 3-5 clientes piloto (EFPCs médias inovadoras dispostas a testar)

| Módulo | Entrega | Critério de sucesso |
|--------|---------|---------------------|
| Cadastro de Favorecidos | Mês 3 | 100% dos tipos de favorecido cadastráveis |
| Lançamentos Financeiros | Mês 4 | Criação, baixa, estorno |
| Contabilidade Essencial | Mês 5 | Fato gerador, lote, disponível, fechamento mensal |
| Remessa Bancária | Mês 5 | Geração de arquivo CNAB400/700 |
| Conciliação Básica | Mês 6 | Importação OFX, Fitid básico |

**Métrica de sucesso:** 3 clientes ativos com 2 meses de fechamento contábil completados no sistema.

#### Fase 2 — Expansão (6 meses)

**Público-alvo:** Escalar para 15-20 clientes

| Módulo | Entrega | Descrição |
|--------|---------|-----------|
| Conciliação Avançada | Mês 8 | Fitid inteligente, aprendizado de padrões |
| Obrigações Fiscais | Mês 9 | EFD, REINF automáticos |
| Portal do Participante | Mês 10 | Consulta de saldo, extrato, solicitações |
| Gestão de Documentos | Mês 10 | Anexo a lançamentos, workflow de aprovação |
| API Pública | Mês 11 | API REST para integração com sistemas de RH |
| Relatórios e BI | Mês 12 | Dashboards gerenciais, exportação |

#### Fase 3 — Aceleração (12 meses)

**Público-alvo:** 50+ clientes

| Entrega | Descrição |
|---------|-----------|
| Marketplace de integrações | Múltiplos bancos, sistemas de RH, custodiantes |
| Benchmarking entre fundos | Painel comparativo anônimo |
| Motor de regras de custeio | Configuração por negócio (sem TI) |
| Gestão de liquidez | Projeção de fluxo de caixa |
| Simulação atuarial | Cenários de custeio integrados |
| Conciliação de investimentos | Posições automáticas de custodiantes |
| App mobile (assinatura de pagamentos) | Aprovação de remessas pelo celular |
| IA para conciliação e anomalias | Detecção de padrões suspeitos |

#### Fase 4 — Plataforma (12+ meses)

- **EFPC como plataforma**: terceiros desenvolvem módulos no marketplace
- **White-label**: outras empresas de software revendem o sistema com sua marca
- **Expansão para outros segmentos**: fundos de investimento, clubes de investimento, family offices

### 10.6. Estrutura de Times para o SaaS

| Time | Responsabilidade | Tamanho sugerido |
|------|-----------------|------------------|
| **Produto** | Roadmap, pesquisa com clientes, especificação | 1 PM + 1 analista de negócios |
| **Backend (Core)** | Domínio contábil, tesouraria, fiscal | 4-6 devs (incluindo 1 senior de domínio) |
| **Backend (Plataforma)** | Multi-tenancy, autenticação, API pública, billing | 2-3 devs |
| **Frontend** | Interface web, portal do participante | 3-4 devs |
| **Integrações** | Conectores bancários, sistemas de RH, governo | 2 devs |
| **DevOps / Infraestrutura** | Cloud, CI/CD, banco de dados, segurança | 2 devs (1 SRE) |
| **Sucesso do Cliente** | Onboarding, treinamento, suporte | 2-3 CS (cresce com número de clientes) |
| **Comercial** | Vendas, pré-vendas técnica, demonstrações | 2 vendedores + 1 pré-vendas |
| **Regulatório / Compliance** | Acompanhamento de normas PREVIC, Receita | 1 especialista (parcial ou consultor) |

**Total estimado:** 18-24 pessoas para a fase de crescimento.

### 10.7. Análise de Risco do Modelo SaaS

| Risco | Probabilidade | Impacto | Mitigação |
|-------|--------------|---------|-----------|
| **Adesão lenta do mercado** (EFPCs são conservadoras) | Alta | Alto | Piloto com 3-5 clientes inovadores, case de sucesso, período de paralelismo |
| **Cada cliente exige customização** | Alta | Alto | Produto altamente configurável (fato gerador, plano de contas, rateio); recusar customização por código |
| **Concorrentes lançam SaaS similar** | Média | Médio | Rede de benchmarking + compliance como serviço são barreiras difíceis de copiar |
| **Mudança regulatória abrupta** | Média | Alto | Time de compliance dedicado monitorando PREVIC, Receita Federal; atualizações entregues em semanas |
| **Churn por migração mal-sucedida** | Alta | Muito Alto | Ferramenta de auto-migração, período de paralelismo de 60 dias, CS dedicado no onboarding |
| **Dados sensíveis em nuvem** | Média | Alto | Certificação ISO 27001, criptografia, nuvem privada opcional para enterprise |
| **Concentração de receita em poucos clientes** | Alta (início) | Alto | Estratégia de expansão para 30+ clientes em 3 anos; limite de 15% da receita por cliente |

### 10.8. Métricas-Chave do SaaS

| Métrica | Meta Ano 1 | Meta Ano 2 | Meta Ano 3 |
|---------|-----------|-----------|-----------|
| **Clientes ativos** | 5 | 20 | 50 |
| **ARR (Annual Recurring Revenue)** | R$ 500k | R$ 2,5M | R$ 8M |
| **MRR médio por cliente** | R$ 8k | R$ 10k | R$ 13k |
| **Churn mensal** | < 5% | < 2% | < 1% |
| **NPS** | > 30 | > 50 | > 60 |
| **Tempo de onboarding** | 60 dias | 30 dias | 15 dias |
| **Taxa de automação de conciliação** | 70% | 85% | 92% |
| **Tempo de fechamento contábil no sistema** | 10 dias | 5 dias | 2 dias |
| **Participantes cadastrados na plataforma** | 100k | 500k | 1,5M |

### 10.9. Resumo da Estratégia SaaS

```
OPORTUNIDADE:
  Mercado de ~250-300 EFPCs no Brasil
  Nenhum SaaS moderno dominante
  Maioria usa sistemas legados ou planilhas
  Regulamentação cada vez mais complexa

DIFERENCIAIS:
  Compliance como Serviço (EFD, REINF automáticos)
  Rede de Benchmarking entre fundos
  Motor de parametrização contábil (sem TI)
  Marketplace de integrações
  Preço acessível para médias/pequenas

MODELO:
  SaaS multi-tenant com 3 tiers (Starter/Business/Enterprise)
  Precificação: base + por participante + módulos
  Land & Expand: entra pela conciliação, expande para contabilidade completa
  Onboarding acelerado com conectores de migração

META:
  50 clientes em 3 anos
  R$ 8M de ARR
  92% de automação de conciliação
  Plataforma aberta para terceiros no ano 4
```

---

*Documento gerado em 2026-06-22*
*Domínio mapeado com base na análise do código-fonte do projeto dataa-tesouraria*
