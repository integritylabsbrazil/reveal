# Modulo: Identity & Auth

## Objetivo de Negocio
Gerenciar quem acessa o sistema e o que cada usuario pode fazer: administradores do inquilino, operadores, participantes, prestadores e auditores. Cada perfil tem acesso a funcionalidades especificas.

## O que Existe nos Legados

### dataa-tesouraria
- Cadastro basico de usuarios com login e senha
- Grupos de usuario para organizar permissoes
- Perfis fixos: administrador, operador, consulta
- Nao ha acesso para participantes externos

### mapsdataa-previdenciario
- Usuarios com email e senha
- Perfis administrativos
- Permissoes granulares por entidade de negocio
- Participantes nao tem acesso ao sistema

## Lacuna de Mercado
- Acesso do participante ao proprio cadastro e extrato (autosservico)
- Aprovacao em duas etapas para operacoes sensiveis
- Bloqueio automatico apos tentativas de acesso invalidas
- Registro completo de quem acessou o que e quando
- Convite para prestadores e auditores com acesso limitado

## Regras de Negocio
1. Todo acesso registra data, horario e o que foi acessado
2. Apos 5 tentativas de login com senha errada, acesso e bloqueado por 15 minutos
3. Sessao expira apos periodo de inatividade (configuravel por inquilino)
4. Usuarios podem ter papeis diferentes em fundos diferentes
5. Participante acessa apenas seus proprios dados
6. Operacao critica (resgate, portabilidade, alteracao cadastral) requer aprovacao de segundo usuario

## Criterios de Aceitacao
1. Usuario operador acessa o sistema com email e senha
2. Participante acessa o sistema e ve apenas seus dados e extrato
3. Operacao de resgate precisa ser aprovada por um segundo usuario
4. Apos 5 tentativas erradas, usuario fica bloqueado por 15 minutos
5. Auditoria mostra quem acessou, quando e o que fez
6. Administrador convida prestador externo com acesso limitado a um modulo especifico
