# Contexto do Projeto — dataa-tesouraria

Gerado automaticamente em 2026-05-20 22:26:41

---

## Stack

| Tecnologia | Versao |
|------------|--------|
| Linguagem | Java |
| Build | maven |

> Consulte o `AGENTS.md` do projeto para versoes exatas (Spring Boot, Java, etc.).

## Arquitetura

Package-by-Feature com padrao de modularizacao por funcionalidade.
Cada feature contem seus proprios controller, service, domain, repository.

> Consulte o `AGENTS.md` do projeto para detalhes arquiteturais especificos.

## Pacote Base

`com.maps.dataa.tesouraria`

## Estrutura de Diretorios

```
java/
com/
  maps/
    dataa/
      tesouraria/
        filtro/
        contabilidade/
        numeracao/
        handler/
          APIExceptionMessages.java
          ControllerExceptionHandler.java
          KeycloakLogoutHandler.java
        favorecido/
        custeio/
        conciliacao/
        instituicaoFinanceira/
        exportador/
        plano/
        remessa/
        efd/
        integracao/
        cep/
        eventoAdicional/
        departamento/
        aplicacaoResgate/
        perfilInvestimento/
        contaContabil/
        naturezaFinanceira/
        trilhaauditoria/
        centroCusto/
        retencao/
        lancamento/
        logging/
          LogErrorAppender.java
        config/
        agencia/
        common/
        processos/
        importacao/
        convenioBancario/
        fechamentoFinanceiro/
        logCarga/
```

## Padroes de Controllers

### Anotacoes de Classe

- `CommonsLog`
- `RequestMapping("/agencia")`
- `RequestMapping("/centro-custo")`
- `RequestMapping("/cep/")`
- `RequestMapping("/codigo-reinf")`
- `RequestMapping("/conta-contabil-calculo-cota")`
- `RequestMapping("/criterio-rateio")`
- `RequestMapping("/custeio")`
- `RequestMapping("/departamento")`
- `RequestMapping("/erros")`
- `RequestMapping("/evento/adicional")`
- `RequestMapping("/fato-gerador")`
- `RequestMapping("/favorecido")`
- `RequestMapping("/favorecido/associacao-plano-participante")`
- `RequestMapping("/favorecido/participante")`
- `RequestMapping("/favorecido/patrocinador-instituidor")`
- `RequestMapping("/fechamento-contabil-consolidado")`
- `RequestMapping("/fechamento-financeiro")`
- `RequestMapping("/fechamento-financeiro/controle-envio")`
- `RequestMapping("/feriado")`
- `RequestMapping("/fornecedor")`
- `RequestMapping("/gerar-remessa")`
- `RequestMapping("/health")`
- `RequestMapping("/historico-cota")`
- `RequestMapping("/importacao")`
- `RequestMapping("/instituicao-financeira")`
- `RequestMapping("/lancamento")`
- `RequestMapping("/lancamento-contabil")`
- `RequestMapping("/lancamento-simples")`
- `RequestMapping("/monitor-integracao-contabil")`
- `RequestMapping("/movimento-extra-contabil")`
- `RequestMapping("/natureza-financeira")`
- `RequestMapping("/numeracao")`
- `RequestMapping("/parametrizacao")`
- `RequestMapping("/parametro-retencao")`
- `RequestMapping("/perfil-investimento")`
- `RequestMapping("/pesquisa")`
- `RequestMapping("/planificacao")`
- `RequestMapping("/plano-beneficios")`
- `RequestMapping("/plano/gestao-administrativa")`
- `RequestMapping("/remessa")`
- `RequestMapping("/retencao")`
- `RequestMapping("baixa-lancamento")`
- `RequestMapping("codigo-retencao")`
- `RequestMapping("numero-sequencial")`
- `RequestMapping("processamento-calculo-cota")`
- `RequestMapping("processo")`
- `RequiredArgsConstructor`
- `RestController`
- `RestControllerAdvice`
- `Tag(name = "Associação Plano Participante")`
- `Tag(name = "Base Custeio")`
- `Tag(name = "Centro de Custo")`
- `Tag(name = "Conta contábil cálculo cota")`
- `Tag(name = "Critério rateio")`
- `Tag(name = "Custeio")`
- `Tag(name = "Código Retenção")`
- `Tag(name = "Departamento")`
- `Tag(name = "Fato Gerador", description = "Define o contexto de parametrização dos itens: histórico, lote.")`
- `Tag(name = "Favorecido Participante")`
- `Tag(name = "Favorecido Patrocinador/Instituidor")`
- `Tag(name = "Favorecido")`
- `Tag(name = "Fechamento Contábil Consolidado")`
- `Tag(name = "Fechamento Financeiro")`
- `Tag(name = "Feriado")`
- `Tag(name = "Gerar Remessa")`
- `Tag(name = "Histórico cota")`
- `Tag(name = "Importação")`
- `Tag(name = "Instituição Financeira")`
- `Tag(name = "Lancamento Contábil")`
- `Tag(name = "Lancamento Simples")`
- `Tag(name = "Lancamento")`
- `Tag(name = "Monitor Integração Contábil")`
- `Tag(name = "Monitor de erros")`
- `Tag(name = "Movimento Extra Contábil")`
- `Tag(name = "Natureza Financeira")`
- `Tag(name = "Numeração")`
- `Tag(name = "Parametrização", description = "Define o contexto de parametrização dos itens: histórico, lote, disponivel.")`
- `Tag(name = "Parametrização", description = "Define o contexto de parametrização dos itens: histórico, lote.")`
- `Tag(name = "Parâmetro de Retenção EFD")`
- `Tag(name = "Perfil Investimento")`
- `Tag(name = "Pesquisa Básica")`
- `Tag(name = "Planificacao Contabil")`
- `Tag(name = "Planificação")`
- `Tag(name = "Plano Benefícios")`
- `Tag(name = "Processamento cálculo cota")`
- `Tag(name = "Remessa")`
- `Tag(name = "Retenção")`
- `Validated`

### Anotacoes de Metodo

- `@GetMapping`
- `@Operation`

### Endpoints Encontrados

| Anotacao | Path |
|----------|------|
| @RequestMapping | /agencia |
| @RequestMapping | /centro-custo |
| @RequestMapping | /cep/ |
| @RequestMapping | /codigo-reinf |
| @RequestMapping | /conta-contabil-calculo-cota |
| @RequestMapping | /criterio-rateio |
| @RequestMapping | /custeio |
| @RequestMapping | /departamento |
| @RequestMapping | /erros |
| @RequestMapping | /evento/adicional |
| @RequestMapping | /fato-gerador |
| @RequestMapping | /favorecido |
| @RequestMapping | /favorecido/associacao-plano-participante |
| @RequestMapping | /favorecido/participante |
| @RequestMapping | /favorecido/patrocinador-instituidor |
| @RequestMapping | /fechamento-contabil-consolidado |
| @RequestMapping | /fechamento-financeiro |
| @RequestMapping | /fechamento-financeiro/controle-envio |
| @RequestMapping | /feriado |
| @RequestMapping | /fornecedor |
| @RequestMapping | /gerar-remessa |
| @RequestMapping | /health |
| @RequestMapping | /historico-cota |
| @RequestMapping | /importacao |
| @RequestMapping | /instituicao-financeira |
| @RequestMapping | /lancamento |
| @RequestMapping | /lancamento-contabil |
| @RequestMapping | /lancamento-simples |
| @RequestMapping | /monitor-integracao-contabil |
| @RequestMapping | /movimento-extra-contabil |
| @RequestMapping | /natureza-financeira |
| @RequestMapping | /numeracao |
| @RequestMapping | /parametrizacao |
| @RequestMapping | /parametro-retencao |
| @RequestMapping | /perfil-investimento |
| @RequestMapping | /pesquisa |
| @RequestMapping | /planificacao |
| @RequestMapping | /plano-beneficios |
| @RequestMapping | /plano/gestao-administrativa |
| @RequestMapping | /remessa |
| @RequestMapping | /retencao |
| @RequestMapping | baixa-lancamento |
| @RequestMapping | codigo-retencao |
| @RequestMapping | numero-sequencial |
| @RequestMapping | processamento-calculo-cota |
| @RequestMapping | processo |
| DeleteMapping | /disponivel/{id} |
| DeleteMapping | /evento-contabil/{id} |
| DeleteMapping | /historico/{numero} |
| DeleteMapping | /lote/{id} |
| DeleteMapping | /{id} |
| DeleteMapping | /{numeroRetencao} |
| DeleteMapping | /{numerosLancamento} |
| DeleteMapping | {id} |
| GetMapping | / |
| GetMapping | /autocomplete |
| GetMapping | /autocomplete-crud |
| GetMapping | /autocomplete/participantes |
| GetMapping | /balancete/verificar/{id} |
| GetMapping | /buscar-todos |
| GetMapping | /custeios-pga |
| GetMapping | /detalhe |
| GetMapping | /detalhes-lista/{ids} |
| GetMapping | /detalhes-numero/{numLancamento} |
| GetMapping | /detalhes/{idDados} |
| GetMapping | /disponivel |
| GetMapping | /envio/pesquisar |
| GetMapping | /envio/resumo |
| GetMapping | /envio/totalizador |
| GetMapping | /evento-contabil |
| GetMapping | /evento-contabil/{id} |
| GetMapping | /exportar-csv |
| GetMapping | /exportar-xls |
| GetMapping | /extra-contabil/exportar-xls |
| GetMapping | /filhas |
| GetMapping | /historico |
| GetMapping | /historico/autocomplete |
| GetMapping | /idFav/{idFav} |
| GetMapping | /informacoes |
| GetMapping | /lote |
| GetMapping | /modelos |
| GetMapping | /natureza-evento/autocomplete |
| GetMapping | /parametrizacao |
| GetMapping | /pesquisar |
| GetMapping | /pga-padrao |
| GetMapping | /ping |
| GetMapping | /planos-sem-custeio |
| GetMapping | /projetado |
| GetMapping | /projetado/detalhe |
| GetMapping | /proximo-valor |
| GetMapping | /rastrear/{idDados} |
| GetMapping | /realizado |
| GetMapping | /resumo |
| GetMapping | /retorno/pesquisar |
| GetMapping | /retorno/resumo |
| GetMapping | /tipos |
| GetMapping | /tipos/mapa |
| GetMapping | /totalizador |
| GetMapping | /ui/security |
| GetMapping | /{id} |
| GetMapping | /{id}/memoria-calculo/exportar-pdf |
| GetMapping | /{numero}/rastreamentos |
| GetMapping | autocomplete |
| GetMapping | gerar-todos/resumo |
| GetMapping | gerar/resumo |
| GetMapping | integracao/resumo |
| GetMapping | rastreamento/{identificador} |
| GetMapping | rastreamento/{numLancamento} |
| GetMapping | rastreamento/{numeroMovimento} |
| GetMapping | resumo |
| GetMapping | resumo-detalhado |
| GetMapping | {cep} |
| GetMapping | {identificador}/rastreamento |
| GetMapping | {id}/rastreamento |
| PostMapping | / |
| PostMapping | /disponivel |
| PostMapping | /envio/reenviar-selecionados |
| PostMapping | /envio/validar |
| PostMapping | /evento-contabil |
| PostMapping | /ferramenta |
| PostMapping | /gerar-lancamento |
| PostMapping | /historico |
| PostMapping | /lote |
| PostMapping | /lote/lancamento |
| PostMapping | /pesquisar |
| PostMapping | /planilha |
| PostMapping | /reenviar-selecionados |
| PostMapping | /retorno/reenviar-selecionados |
| PostMapping | /retorno/validar |
| PostMapping | /validar |
| PostMapping | /validar-endereco |
| PostMapping | /validar-fitid |
| PostMapping | fatos-pendentes |
| PostMapping | fatos-todos-pendentes |
| PutMapping | / |
| PutMapping | /agrupar |
| PutMapping | /autorizar/{ids} |
| PutMapping | /baixar |
| PutMapping | /baixar-parcial |
| PutMapping | /cancelar |
| PutMapping | /conciliacao |
| PutMapping | /devolver-todos |
| PutMapping | /devolver/{ids} |
| PutMapping | /disponivel |
| PutMapping | /dividir |
| PutMapping | /enviar |
| PutMapping | /enviar-parcial |
| PutMapping | /evento-contabil |
| PutMapping | /gerar-todos |
| PutMapping | /gerar/{ids} |
| PutMapping | /historico |
| PutMapping | /integracao |
| PutMapping | /integracao-todos |
| PutMapping | /lote |
| PutMapping | /rejeitar |
| PutMapping | /reverter |
| PutMapping | /reverter/{ids} |
| PutMapping | /validar |
| PutMapping | /validar/{ids} |
| PutMapping | /{id} |
| PutMapping | /{id}/documentos |
| PutMapping | /{numRemessa}/cancelar |
| PutMapping | /{numeroRemessa}/retorno |
| PutMapping | /{numero}/cancelar |
| PutMapping | calcular |
| PutMapping | calcular-todos |
| PutMapping | cancelar |
| PutMapping | cancelar-todos |
| PutMapping | encerramento-exercicio |
| PutMapping | encerramento-exercicio/cancelar |
| PutMapping | fechamento |
| PutMapping | fechamento-todos |
| PutMapping | gerar |
| PutMapping | gerar-todos |
| PutMapping | integracao/atualizar |
| PutMapping | integracao/cancelar/{idDadosBasicos} |
| PutMapping | integracao/validar |
| PutMapping | reabertura |
| PutMapping | reabertura-todos |
| PutMapping | retorno/selecionados |
| PutMapping | {id} |
| RequestMapping | /agencia |
| RequestMapping | /centro-custo |
| RequestMapping | /cep/ |
| RequestMapping | /codigo-reinf |
| RequestMapping | /conta-contabil-calculo-cota |
| RequestMapping | /criterio-rateio |
| RequestMapping | /custeio |
| RequestMapping | /departamento |
| RequestMapping | /erros |
| RequestMapping | /evento/adicional |
| RequestMapping | /fato-gerador |
| RequestMapping | /favorecido |
| RequestMapping | /favorecido/associacao-plano-participante |
| RequestMapping | /favorecido/participante |
| RequestMapping | /favorecido/patrocinador-instituidor |
| RequestMapping | /fechamento-contabil-consolidado |
| RequestMapping | /fechamento-financeiro |
| RequestMapping | /fechamento-financeiro/controle-envio |
| RequestMapping | /feriado |
| RequestMapping | /fornecedor |
| RequestMapping | /gerar-remessa |
| RequestMapping | /health |
| RequestMapping | /historico-cota |
| RequestMapping | /importacao |
| RequestMapping | /instituicao-financeira |
| RequestMapping | /lancamento |
| RequestMapping | /lancamento-contabil |
| RequestMapping | /lancamento-simples |
| RequestMapping | /monitor-integracao-contabil |
| RequestMapping | /movimento-extra-contabil |
| RequestMapping | /natureza-financeira |
| RequestMapping | /numeracao |
| RequestMapping | /parametrizacao |
| RequestMapping | /parametro-retencao |
| RequestMapping | /perfil-investimento |
| RequestMapping | /pesquisa |
| RequestMapping | /planificacao |
| RequestMapping | /plano-beneficios |
| RequestMapping | /plano/gestao-administrativa |
| RequestMapping | /remessa |
| RequestMapping | /retencao |
| RequestMapping | baixa-lancamento |
| RequestMapping | codigo-retencao |
| RequestMapping | numero-sequencial |
| RequestMapping | processamento-calculo-cota |
| RequestMapping | processo |

### Exemplos

- `com.maps.dataa.tesouraria.filtro.controller.FiltroController`  — `src/main/java/com/maps/dataa/tesouraria/filtro/controller/FiltroController.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.controller.FechamentoContabilController`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/controller/FechamentoContabilController.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentocontabilconsolidado.controller.FechamentoContabilConsolidadoController`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentocontabilconsolidado/controller/FechamentoContabilConsolidadoController.java`
- `com.maps.dataa.tesouraria.contabilidade.disponivel.controller.DisponivelController`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/disponivel/controller/DisponivelController.java`
- `com.maps.dataa.tesouraria.contabilidade.contaExtraContabil.controller.ContaExtraContabilController`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/contaExtraContabil/controller/ContaExtraContabilController.java`

## Padroes de Services

### Anotacoes

- `AllArgsConstructor`
- `CommonsLog`
- `Component`
- `ConditionalOnExpression("#{'${tesouraria.system.security.authentication.protocol}' eq 'NOAUTH' or !${tesouraria.system.sysadmin.active}}")`
- `ConditionalOnExpression("#{'${tesouraria.system.security.authentication.protocol}' eq 'OPENID' and ${tesouraria.system.sysadmin.active}}")`
- `Deprecated(since = "2025.12", forRemoval = true)`
- `Getter`
- `Mapper`
- `NoArgsConstructor(access = AccessLevel.PRIVATE)`
- `Order(1)`
- `Order(10)`
- `Order(11)`
- `Order(12)`
- `Order(13)`
- `Order(14)`
- `Order(15)`
- `Order(16)`
- `Order(2)`
- `Order(3)`
- `Order(4)`
- `Order(5)`
- `Order(6)`
- `Order(7)`
- `Order(8)`
- `Order(9)`
- `Profile("!" + TesourariaProfiles.PLANILHAS)`
- `Profile(TesourariaProfiles.INTEGRACAO_BB)`
- `Profile(TesourariaProfiles.PLANILHAS)`
- `RequiredArgsConstructor`
- `Service`
- `Transactional(readOnly = true)`
- `Validated`

### Exemplos

- `com.maps.dataa.tesouraria.filtro.service.FiltroService`  — `src/main/java/com/maps/dataa/tesouraria/filtro/service/FiltroService.java`
- `com.maps.dataa.tesouraria.filtro.action.FiltroValidatorAction`  — `src/main/java/com/maps/dataa/tesouraria/filtro/action/FiltroValidatorAction.java`
- `com.maps.dataa.tesouraria.filtro.action.FiltroGetAction`  — `src/main/java/com/maps/dataa/tesouraria/filtro/action/FiltroGetAction.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.service.FechamentoContabilService`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/service/FechamentoContabilService.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.service.FechamentoContabilManager`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/service/FechamentoContabilManager.java`

## Padroes de Entities

### Anotacoes

- `Alias("CENCUST")`
- `Alias("COLAB")`
- `Alias("CONBAC")`
- `Alias("CONSBACS")`
- `Alias("CONSBALCC")`
- `Alias("CONSBALP")`
- `Alias("CONSBALPAT")`
- `Alias("CONT_CNTR")`
- `Alias("CONT_ENT")`
- `Alias("CONT_RESP")`
- `Alias("CRIRAT")`
- `Alias("CRNF4020")`
- `Alias("DISP")`
- `Alias("DPTMTO")`
- `Alias("EINTB")`
- `Alias("ERRIMP")`
- `Alias("ERRPRC")`
- `Alias("EVEADC")`
- `Alias("FATGER")`
- `Alias("FATGEREVT")`
- `Alias("FATGEREVTAD")`
- `Alias("FATGERNATFIN")`
- `Alias("FATGERRET")`
- `Alias("FAVOR")`
- `Alias("GEREINF")`
- `Alias("HICOTA")`
- `Alias("HISTORICO")`
- `Alias("LANCONT")`
- `Alias("LOTE")`
- `Alias("MCHITC")`
- `Alias("MODIMP")`
- `Alias("NATFIN")`
- `Alias("NMRC")`
- `Alias("NUMSEQ")`
- `Alias("PARAMEVCONT")`
- `Alias("PERINV")`
- `Alias("PIX")`
- `Alias("PLANO")`
- `Alias("PLNFC")`
- `Alias("POSATHC")`
- `Alias("PRCCT")`
- `Alias("PRCSS")`
- `Alias("PRMPROC")`
- `Alias("RESP_ENT")`
- `Alias("RMB")`
- `Alias("TRANS")`
- `Alias("imparq")`
- `AllArgsConstructor`
- `Builder`
- `CommonsLog`
- `Component`
- `Converter`
- `Converter(autoApply = true)`
- `Data`
- `Embeddable`
- `Entity`
- `EqualsAndHashCode(callSuper = true)`
- `FilterAlias("CodigoRetencao")`
- `FilterAlias("Lote")`
- `FilterAlias("ParametroEventoContabil")`
- `Getter`
- `MappedSuperclass`
- `NoArgsConstructor`
- `NoArgsConstructor(access = AccessLevel.PRIVATE)`
- `Repository`
- `RequiredArgsConstructor`
- `RestControllerAdvice`
- `SequenceGenerator(name =  "SEQ_PRMPROC", sequenceName = "SEQ_PRMPROC")`
- `SequenceGenerator(name = "SEQ_CENTRO_CUSTO", sequenceName = "SEQ_CENTRO_CUSTO")`
- `SequenceGenerator(name = "SEQ_CNTDR", sequenceName = "SEQ_CNTDR")`
- `SequenceGenerator(name = "SEQ_CNT_CLC_COTA", sequenceName = "SEQ_CNT_CLC_COTA")`
- `SequenceGenerator(name = "SEQ_COLABORADOR", sequenceName = "SEQ_COLABORADOR")`
- `SequenceGenerator(name = "SEQ_CONS_BALANCETE", sequenceName = "SEQ_CONS_BALANCETE")`
- `SequenceGenerator(name = "SEQ_CONS_BAL_CENTRO_CUSTO", sequenceName = "SEQ_CONS_BAL_CENTRO_CUSTO")`
- `SequenceGenerator(name = "SEQ_CONS_BAL_CUSTEIO", sequenceName = "SEQ_CONS_BAL_CUSTEIO")`
- `SequenceGenerator(name = "SEQ_CONS_BAL_PATROCINADOR", sequenceName = "SEQ_CONS_BAL_PATROCINADOR")`
- `SequenceGenerator(name = "SEQ_CONS_BAL_PERFIL", sequenceName = "SEQ_CONS_BAL_PERFIL")`
- `SequenceGenerator(name = "SEQ_CONTATO_CONTADOR", sequenceName = "SEQ_CONTATO_CONTADOR")`
- `SequenceGenerator(name = "SEQ_CONTATO_RESP", sequenceName = "SEQ_CONTATO_RESP")`
- `SequenceGenerator(name = "SEQ_CRIRAT", sequenceName = "SEQ_CRIRAT")`
- `SequenceGenerator(name = "SEQ_CRNF4020", sequenceName = "SEQ_CRNF4020")`
- `SequenceGenerator(name = "SEQ_DEPARTAMENTO", sequenceName = "SEQ_DEPARTAMENTO")`
- `SequenceGenerator(name = "SEQ_DISPONIVEL", sequenceName = "SEQ_DISPONIVEL")`
- `SequenceGenerator(name = "SEQ_ERRPRC", sequenceName = "SEQ_ERRPRC")`
- `SequenceGenerator(name = "SEQ_EVENTO_ADICIONAL", sequenceName = "SEQ_EVENTO_ADICIONAL")`
- `SequenceGenerator(name = "SEQ_FATO_GERADOR", sequenceName = "SEQ_FATO_GERADOR")`
- `SequenceGenerator(name = "SEQ_FATO_GERADOR_EVT", sequenceName = "SEQ_FATO_GERADOR_EVT")`
- `SequenceGenerator(name = "SEQ_FATO_GERADOR_EVT_ADICIONAL", sequenceName = "SEQ_FATO_GERADOR_EVT_ADICIONAL")`
- `SequenceGenerator(name = "SEQ_FATO_GERADOR_NATUREZA_FINANCEIRA", sequenceName = "SEQ_FATO_GERADOR_NATUREZA_FINANCEIRA")`
- `SequenceGenerator(name = "SEQ_FATO_GERADOR_RETENCAO", sequenceName = "SEQ_FATO_GERADOR_RETENCAO")`
- `SequenceGenerator(name = "SEQ_FAVORECIDO", sequenceName = "SEQ_FAVORECIDO")`
- `SequenceGenerator(name = "SEQ_GERACAO_REINF", sequenceName = "SEQ_GERACAO_REINF")`
- `SequenceGenerator(name = "SEQ_HISTORICO_COTA", sequenceName = "SEQ_HISTORICO_COTA")`
- `SequenceGenerator(name = "SEQ_IMPARQ", sequenceName = "SEQ_IMPARQ")`
- `SequenceGenerator(name = "SEQ_LGERR", sequenceName = "SEQ_LGERR")`
- `SequenceGenerator(name = "SEQ_LOTE", sequenceName = "SEQ_LOTE")`
- `SequenceGenerator(name = "SEQ_MEMORIA_CALCULO_HISTORICO_COTA", sequenceName = "SEQ_MEMORIA_CALCULO_HISTORICO_COTA")`
- `SequenceGenerator(name = "SEQ_NATFIN", sequenceName = "SEQ_NATFIN")`
- `SequenceGenerator(name = "SEQ_NMRC", sequenceName = "SEQ_NMRC")`
- `SequenceGenerator(name = "SEQ_NUMSEQ", sequenceName = "SEQ_NUMSEQ")`
- `SequenceGenerator(name = "SEQ_PARAMETRO_EVENTO_CONTABIL", sequenceName = "SEQ_PARAMETRO_EVENTO_CONTABIL")`
- `SequenceGenerator(name = "SEQ_PERFIL_INVESTIMENTO", sequenceName = "SEQ_PERFIL_INVESTIMENTO")`
- `SequenceGenerator(name = "SEQ_PIX", sequenceName = "SEQ_PIX")`
- `SequenceGenerator(name = "SEQ_PLANO", sequenceName = "SEQ_PLANO")`
- `SequenceGenerator(name = "SEQ_PLNFC", sequenceName = "SEQ_PLNFC")`
- `SequenceGenerator(name = "SEQ_POSICAO_ATUAL_HISTORICO_COTA", sequenceName = "SEQ_POSICAO_ATUAL_HISTORICO_COTA")`
- `SequenceGenerator(name = "SEQ_PRCSS", sequenceName = "SEQ_PRCSS")`
- `SequenceGenerator(name = "SEQ_PROCESSAMENTO_CALCULO_COTA", sequenceName = "SEQ_PROCESSAMENTO_CALCULO_COTA")`
- `SequenceGenerator(name = "SEQ_RMB", sequenceName = "SEQ_RMB")`
- `SequenceGenerator(name = "SEQ_RSPNENT", sequenceName = "SEQ_RSPNENT")`
- `SequenceGenerator(name = "SEQ_TRANSFERENCIA", sequenceName = "SEQ_TRANSFERENCIA")`
- `SequenceGenerator(name="SEQ_HISTORICO", sequenceName = "SEQ_HISTORICO")`
- `SequenceGenerator(sequenceName = "SEQ_EINTB", name = "SEQ_EINTB")`
- `SequenceGenerator(sequenceName = "SEQ_ERRIMP", name = "SEQ_ERRIMP")`
- `SequenceGenerator(sequenceName = "SEQ_MODIMP", name = "SEQ_MODIMP")`
- `Service`
- `Setter`
- `SuperBuilder`
- `Table(name = "CENTRO_CUSTO")`
- `Table(name = "COLABORADOR")`
- `Table(name = "CONTADOR_ENTIDADE")`
- `Table(name = "CONTATO_CONTADOR")`
- `Table(name = "CONTATO_RESPONSAVEL")`
- `Table(name = "CONTA_CONTABIL_CALCULO_COTA")`
- `Table(name = "CRITERIO_RATEIO")`
- `Table(name = "DISPONIVEL")`
- `Table(name = "ENVIO_INTEGRACAO_BANCARIA")`
- `Table(name = "ERRO_PROCESSO")`
- `Table(name = "FATO_GERADOR")`
- `Table(name = "FATO_GERADOR_EVT")`
- `Table(name = "FATO_GERADOR_EVT_ADICIONAL")`
- `Table(name = "FATO_GERADOR_NATUREZA_FINANCEIRA")`
- `Table(name = "FATO_GERADOR_RETENCAO")`
- `Table(name = "GERACAO_REINF")`
- `Table(name = "HISTORICO_COTA")`
- `Table(name = "IMPORTACAO_ARQUIVO")`
- `Table(name = "LOTE")`
- `Table(name = "MEMORIA_CALCULO_HISTORICO_COTA")`
- `Table(name = "MODELO_IMPORTACAO")`
- `Table(name = "NATUREZA_FINANCEIRA")`
- `Table(name = "NUMERO_SEQUENCIAL")`
- `Table(name = "PARAMETRO_PROCESSO")`
- `Table(name = "PERFIL_INVESTIMENTO")`
- `Table(name = "PIX")`
- `Table(name = "PLANIFICACAO")`
- `Table(name = "PLANO")`
- `Table(name = "POSICAO_ATUAL_HISTORICO_COTA")`
- `Table(name = "PROCESSAMENTO_CALCULO_COTA")`
- `Table(name = "PROCESSO")`
- `Table(name = "RASTREAMENTO_MOVIMENTO_BANCARIO")`
- `Table(name = "RESPONSAVEL_ENTIDADE")`
- `Table(name = "TRANSFERENCIA")`
- `Unique(uniqueName="PARAMEVCONT_UNIQUE", message = "Já existe um evento contábil para o lote, com o mesmo identificador.")`

### Exemplos

- `com.maps.dataa.tesouraria.filtro.repository.FiltroRepository`  — `src/main/java/com/maps/dataa/tesouraria/filtro/repository/FiltroRepository.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.repository.FechamentoContabilRepositoryCustomImpl`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/repository/FechamentoContabilRepositoryCustomImpl.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.domain.FechamentoContabil`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/domain/FechamentoContabil.java`

## Padroes de DTOs

### Anotacoes

- `AllArgsConstructor`
- `Builder`
- `CommonsLog`
- `Data`
- `EqualsAndHashCode(callSuper = true)`
- `Getter`
- `JsonIgnoreProperties(ignoreUnknown = true)`
- `NoArgsConstructor`
- `Setter`
- `SuperBuilder`
- `Valid`
- `Validated`

### Exemplos

- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.model.ValidacaoFechamentoContabilInput`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/model/ValidacaoFechamentoContabilInput.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.model.FechamentoContabilOutput`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/model/FechamentoContabilOutput.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.model.FechamentoContabilFilter`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/model/FechamentoContabilFilter.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.model.FechamentoContabilReaberturaTodosInput`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/model/FechamentoContabilReaberturaTodosInput.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.model.FechamentoFatoPendenteInput`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/model/FechamentoFatoPendenteInput.java`

## Padroes de Repositories

### Anotacoes

- `Component`
- `Repository`
- `RequiredArgsConstructor`
- `Resource`

### Exemplos

- `com.maps.dataa.tesouraria.filtro.repository.FiltroRepository`  — `src/main/java/com/maps/dataa/tesouraria/filtro/repository/FiltroRepository.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.repository.FechamentoContabilRepositoryCustom`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/repository/FechamentoContabilRepositoryCustom.java`
- `com.maps.dataa.tesouraria.contabilidade.fechamentoContabil.repository.FechamentoContabilRepository`  — `src/main/java/com/maps/dataa/tesouraria/contabilidade/fechamentoContabil/repository/FechamentoContabilRepository.java`

## Pacotes Encontrados

```
Total de classes analisadas: ~14 pacotes
- com.maps.dataa.tesouraria.contabilidade
- com.maps.dataa.tesouraria.filtro
```

---

*Contexto gerado em 2026-05-20 22:26:41*
*Regenerar com: `./generate-project-context.sh {name}`*