# Backlog e Kanban — Sprint 2

Este documento é o quadro versionado da Sprint 2. O detalhamento técnico das tasks permanece em [`plano_desenvolvimento_sprint2.md`](plano_desenvolvimento_sprint2.md), e as decisões normativas estão no [`ADR-001`](adr/ADR-001-decisoes-dimensionamento-fotovoltaico.md).

## Épicos

| Épico | Objetivo | User stories |
|---|---|---|
| E1 — Dados FV | Disponibilizar catálogos e recurso solar íntegros, rastreáveis e versionados. | US-PV01, US-PV02 |
| E2 — Motor | Calcular geração, selecionar módulos e validar arranjos/inversores. | US-PV03, US-PV04 |
| E3 — Armazenamento | Dimensionar BESS sem dupla aplicação de DoD e garantir arquitetura compatível. | US-PV05 |
| E4 — Proposta | Persistir snapshots e formar uma proposta e orçamento auditáveis. | US-PV06, US-PV07 |
| E5 — Integração | Expor o fluxo autenticado na API/UI e comprovar qualidade e isolamento. | US-PV08, US-PV09, US-PV10 |

## User stories e critérios de aceite

| ID | Épico | História | Critérios de aceite resumidos | Tasks |
|---|---|---|---|---|
| US-PV01 | Dados FV | Como responsável técnico, quero catálogos reais e rastreáveis para simular com dados auditáveis. | Contagens e schemas mínimos atendidos; IDs únicos; unidades, datas, fontes técnicas e preços BRL validados; carga atômica. | 18, 19, 20, 21 |
| US-PV02 | Dados FV | Como usuário, quero informar/confirmar o HSP para que a simulação preserve a origem do recurso solar. | HSP positivo; unidade, origem, data e modo persistidos; ausência de fonte não gera valor inventado. | 22 |
| US-PV03 | Motor | Como usuário, quero calcular a potência e comparar módulos para atender uma fração do meu consumo. | Consumo vem da residência; fórmulas usam Decimal; quantidade usa `ceil`; resultados incluem unidades e alternativas. | 23, 24 |
| US-PV04 | Motor | Como responsável técnico, quero apenas inversores e strings compatíveis para não orçar uma solução inválida. | Arranjo explícito; potência, Voc e Vmp validados; rejeições estruturadas; preço ordena somente os elegíveis. | 25 |
| US-PV05 | Armazenamento | Como usuário, quero comparar cenários com e sem bateria para atender a autonomia escolhida. | Convenção do ADR-001; 0 h sem bateria; arredondamento para cima; somente inversor compatível quando BESS ativo. | 26, 27 |
| US-PV06 | Proposta | Como usuário, quero um orçamento detalhado para entender a composição do preço. | BOM imutável; valores Decimal; adicionais explícitos; subtotais e total conferidos no servidor. | 28 |
| US-PV07 | Proposta | Como usuário, quero salvar e recuperar propostas sem que mudanças no catálogo alterem o histórico. | Migration upgrade/downgrade; snapshots técnicos/comerciais; CRUD por proprietário; cascata definida. | 17 |
| US-PV08 | Integração | Como cliente autenticado, quero simular e administrar propostas pela API com erros compreensíveis. | Contrato OpenAPI; consumo derivado; 401/404/422/409; autorização centralizada. | 29 |
| US-PV09 | Integração | Como usuário, quero configurar e visualizar o dimensionamento a partir da residência. | Formulário não solicita `C_m`; estados de UI; resumo, strings, BOM, aviso acadêmico e recálculo. | 30, 31 |
| US-PV10 | Integração | Como equipe, queremos evidências automatizadas e documentação reproduzível para liberar a sprint com segurança. | Testes unitários, integração com dois usuários, dois cenários, build e documentação de fontes/premissas. | 32, 33, 34 |

Os critérios completos e evidências esperadas de cada task estão na seção 8 do plano da sprint e fazem parte deste backlog por referência.

## Prioridade e dependências

Prioridades: `P0` bloqueia a fundação ou a segurança do fluxo; `P1` entrega o caminho principal; `P2` consolida experiência, regressão e evidências.

| Task | Épico | Prioridade | Depende de | Estado inicial após TASK-16 |
|---|---|---:|---|---|
| TASK-16 | Transversal | P0 | — | Done |
| TASK-17 | Proposta | P0 | 16 | Review |
| TASK-18 | Dados FV | P0 | 16 | Review |
| TASK-19 | Dados FV | P0 | 16 | Review |
| TASK-20 | Dados FV | P0 | 16 | Review |
| TASK-21 | Dados FV | P0 | 18, 19, 20 | Review |
| TASK-22 | Dados FV | P0 | 16 | Done |
| TASK-23 | Motor | P0 | 22 | Review |
| TASK-24 | Motor | P0 | 21, 23 | Review |
| TASK-25 | Motor | P0 | 19, 21, 24 | Review |
| TASK-26 | Armazenamento | P0 | 20, 21, 23 | Review |
| TASK-27 | Armazenamento | P0 | 25, 26 | Review |
| TASK-28 | Proposta | P1 | 24, 25, 26, 27 | Review |
| TASK-29 | Integração | P1 | 17, 21, 22, 23, 24, 25, 26, 27, 28 | Review |
| TASK-30 | Integração | P1 | contrato estável de 29 | Backlog |
| TASK-31 | Integração | P1 | 28, 29, 30 | Backlog |
| TASK-32 | Integração | P1 | incrementalmente 21–28 | Backlog |
| TASK-33 | Integração | P1 | 17, 29, 30, 31, 32 | Backlog |
| TASK-34 | Integração | P2 | inicia com 18; encerra após 33 | Backlog |

O grafo foi organizado como um DAG. TASK-30 pode começar com mocks somente após estabilização do contrato da TASK-29; isso não autoriza marcar a task como concluída antes da integração real.

## Quadro Kanban

| Backlog | To Do | In Progress | Review | Done |
|---|---|---|---|---|
| TASK-30–TASK-34 | — | — | TASK-17–TASK-21, TASK-23–TASK-29 | TASK-16, TASK-22 |

### Políticas do quadro

- **Backlog:** item ainda bloqueado por dependência ou não comprometido para execução imediata.
- **To Do:** atende à Definition of Ready e não possui dependência bloqueadora.
- **In Progress:** implementação ativa; limite de WIP de 3 tasks para a equipe.
- **Review:** mudança implementada, com testes/evidências anexados; limite de WIP de 3 tasks.
- **Done:** critérios e Definition of Done da task atendidos e integrados.
- Um item bloqueado permanece na coluna atual com o bloqueio registrado; não avança artificialmente.
- A movimentação de uma task deve atualizar este quadro no mesmo pull request.

## Checklist de encerramento da TASK-16

- [x] Cinco épicos definidos.
- [x] User stories ligadas a critérios e tasks.
- [x] Prioridades registradas.
- [x] Dependências registradas e revisadas sem ciclo.
- [x] Colunas e políticas do Kanban definidas.
- [x] Itens liberados por dependência movidos para `To Do`.
- [x] Decisões técnicas da seção 3.2 registradas no ADR-001.
