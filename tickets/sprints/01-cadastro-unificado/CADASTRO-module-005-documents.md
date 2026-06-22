# Modulo: Document Management

## Objetivo de Negocio
Receber, validar e armazenar documentos dos participantes e fundos de forma digital. Documentos como RG, CPF, comprovante de residencia e contratos sao enviados digitalmente, passam por verificacao e ficam disponiveis para consulta.

## O que Existe nos Legados
Nenhum dos legados possui gestao documental integrada. Documentos sao fisicos ou armazenados em pastas de rede.

### dataa-tesouraria
- Referencia a documentos em campos de observacao (texto livre)

### mapsdataa-previdenciario
- Anexos em workflow de processos

## Lacuna de Mercado
Gerenciamento digital de documentos e uma carencia total no setor:
- Participante envia foto do documento pelo celular
- Sistema extrai os dados automaticamente e preenche o cadastro
- Documento passa por validacao antes de ser aceito
- Prazos de guarda conforme legislacao (LGPD)
- Contratos e regulamentos ficam disponiveis para consulta online

## Regras de Negocio
1. Documentos sao classificados por tipo: RG, CPF, comprovante de endereco, contrato, regulamento
2. Ao enviar, o sistema tenta extrair os dados automaticamente para preencher o cadastro
3. Documento precisa ser aprovado antes de ser considerado valido
4. Cada tipo de documento tem prazo de guarda especifico (10 anos para RG, vida do contrato + 5 anos)
5. Participante pode consultar seus proprios documentos a qualquer momento

## Criterios de Aceitacao
1. Participante envia foto do RG e sistema preenche nome e CPF automaticamente
2. Documento enviado passa por fila de aprovacao
3. Aprovador recebe notificacao, analisa e aprova ou rejeita o documento
4. Documento expirado e movido para arquivo morto (nao e apagado)
5. Participante acessa seus documentos pelo aplicativo
