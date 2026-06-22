# Modulo: Members

## Objetivo de Negocio
Unificar FAVORECIDO (tesouraria), PARTICIPANTE (previdenciario), BENEFICIARIO e PATROCINADOR em uma unica entidade "Member" com tipos (PF, PJ, dependente) e papeis (participante, beneficiario, patrocinador, terceiro). Um member pode ter multiplos papeis simultaneamente.

## O que Existe nos Legados

### dataa-tesouraria
- Tabela FAVORECIDO: ~30 colunas (ID, NOME, CPF_CNPJ, TIPO, ATIVO, LOGRADOURO, BAIRRO, CIDADE, UF, CEP, TELEFONE, EMAIL, etc.)
- Tabela ENDERECO: enderecos separados do favorecido
- Tabela PROFISSAO, ESCOLARIDADE, SEXO, ESTADO_CIVIL: dominios auxiliares
- Tabela BENEFICIARIO: vinculado a FAVORECIDO
- Tabela DEPENDENTE: vinculado a FAVORECIDO
- Tabela PATROCINADOR: entidade patrocinadora

### mapsdataa-previdenciario
- Entidade PARTICIPANTE: servidor publico, vinculado a orgao
- Entidade PATROCINADOR: orgao publico, tribunal, poder
- Entidade BENEFICIARIO: vinculado a participante
- Entidade DEPENDENTE: vinculado a beneficiario
- Vinculo: PLANO -> PATROCINADOR -> PARTICIPANTE

## Lacuna de Mercado
- Unificacao real: no legado, uma mesma pessoa pode existir como FAVORECIDO no tesouraria e PARTICIPANTE no previdenciario sem relacao entre si
- Autosservico: participante atualizar seus dados sem passar pelo operador
- Biometria facial: validacao de identidade via selfie vs documento
- Enriquecimento automatico de dados via CPF (API Receita Federal, Serasa)
- Hierarquia de members: grupo economico, holding, subsidiaria

## Regras de Negocio
1. Member tem tipo: PF (pessoa fisica), PJ (pessoa juridica), DEPENDENTE
2. Papeis: PARTICIPANTE, BENEFICIARIO, PATROCINADOR, PRESTADOR, TERCEIRO
3. Um member PF pode ser participante de um fundo e patrocinador de outro
4. CPF/CNPJ e obrigatorio e unico por tenant
5. Dados de contato sao versionados (historico de enderecos, telefones, emails)
6. Documentos comprobatorios sao armazenados no modulo Documents (005)
7. Aprovacao de cadastro pode ser automatica (via integracao Receita) ou manual (workflow)
8. Members inativos nao podem participar de transacoes financeiras

## Criterios de Aceitacao
1. Criacao de member PF com CPF valido enriquece endereco automaticamente via CEP
2. Member PJ permite cadastro de socios com participacao
3. Um member pode ser participante de 2 fundos e patrocinador de 1 ao mesmo tempo
4. Historico de alteracoes cadastrais e mantido com data e autor
5. Busca por member funciona por: CPF/CNPJ, nome (parcial), email, telefone
6. Bloqueio de member inativo impede transacoes

## Dependencias Tecnicas
- 00-Identity (authentication, RBAC para quem pode cadastrar)

## Projetos Legados de Referencia
- Tesouraria: `src/main/java/**/favorecido/`, `src/main/java/**/patrocinador/`, `src/main/java/**/beneficiario/`
- Previdenciario: `core/src/main/java/**/participante/`, `core/src/main/java/**/patrocinador/`, `core/src/main/java/**/beneficiario/`
