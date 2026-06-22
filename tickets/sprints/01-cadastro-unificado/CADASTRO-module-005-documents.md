# Modulo: Document Management

## Objetivo de Negocio
Gerir todo o ciclo de vida de documentos dos members e fundos: upload, OCR, classificacao automatica, validacao, armazenamento seguro e descarte conforme politica de retencao. Substitui a gestao de documentos fisica e descentralizada dos legados.

## O que Existe nos Legados
Nenhum dos legados possui gestao documental integrada. Documentos sao armazenados em pastas de rede ou sistemas externos (SharePoint, Google Drive).

### dataa-tesouraria
- Nao ha modulo de documentos
- Referencia a documentos em campos texto livres (observacao, historico)

### mapsdataa-previdenciario
- Nao ha modulo de documentos
- Referencia a documentos em anexos de workflow (Tabela DOCUMENTO no modulo WORKFLOW)

## Lacuna de Mercado
Gestao documental e um GAP total no mercado de previdencia complementar. Nenhum concorrente oferece:
- OCR automatico com extracao de dados (RG, CPF, comprovante residencia)
- Classificacao por tipo de documento com ML
- Workflow de validacao com aprovacao
- Conformidade com LGPD (retencao, descarte, auditoria)
- Assinatura digital integrada (gov.br, cert digital A1/A3)

## Regras de Negocio
1. Documentos sao classificados por tipo: RG, CPF, COMPROVANTE_ENDERECO, CONTRATO, REGULAMENTO, etc.
2. Cada tipo de documento tem regras de validacao especificas
3. OCR extrai dados e preenche campos do formulario automaticamente
4. Documentos passam por workflow de aprovacao (automatica ou manual)
5. Prazos de retencao por tipo: RG (10 anos), Contrato (vida do contrato + 5 anos)
6. Assinatura digital qualifica o documento juridicamente
7. Documentos sao armazenados com criptografia em repouso (AES-256)

## Criterios de Aceitacao
1. Upload de RG em PDF extrai nome, CPF, data nascimento com acuracia > 90%
2. Workflow de aprovacao: documento pendente -> aprovado/rejeitado com notificacao
3. Politica de retencao: documento expirado e movido para archive (nao deletado)
4. Busca textual em documentos com OCR (full-text search)
5. Assinatura digital via certificado A1 valida documento

## Dependencias Tecnicas
- 001 - Members (documentos sao do member)

## Projetos Legados de Referencia
- Nenhum (dominio novo)
- Referencia: integracao com gov.br para validacao de documentos
