# Plano de Desenvolvimento — Sprint 2

## 1. Objetivo da sprint

Entregar o fluxo completo e autenticado de pré-dimensionamento fotovoltaico por residência, partindo do consumo mensal já calculado pelo sistema até a geração e persistência de uma proposta preliminar com:

- recurso solar (HSP) rastreável;
- potência fotovoltaica requerida;
- módulos e inversor tecnicamente compatíveis;
- armazenamento opcional por baterias;
- orçamento detalhado;
- interface de configuração e resultado;
- testes automatizados e documentação das premissas.

O resultado da sprint deve funcionar nos dois cenários obrigatórios: sistema on-grid sem bateria e sistema com armazenamento e inversor compatível.

## 2. Contexto técnico atual

O plano considera a implementação existente no repositório, e não apenas a arquitetura ideal descrita nos documentos:

- backend em Python 3.10+, FastAPI, Pydantic e SQLAlchemy;
- banco SQLite e criação de tabelas atualmente feita por `Base.metadata.create_all`;
- frontend em React 19, TypeScript e Create React App, servido na porta 3000;
- autenticação JWT e isolamento de residências por usuário já implementados;
- consumo mensal da residência disponível em `GET /properties/{property_id}/consumption-report`;
- testes de API baseados em `unittest`, `TestClient` e SQLite em memória;
- documentação OpenAPI/Swagger gerada pelo FastAPI.

Durante esta sprint, a implementação existente deve ser tratada como fonte de verdade para stack e execução. Divergências de `SPEC.md`, como Vite/porta 5173, não devem motivar uma migração de frontend dentro da Sprint 2.

## 3. Premissas, decisões e limites

### 3.1 Premissas de implementação

- O consumo de referência (`C_m`) será sempre obtido no backend a partir dos equipamentos da residência autenticada; o cliente não poderá substituir esse valor livremente no payload.
- Percentuais serão convertidos para frações antes dos cálculos: por exemplo, 80% = `0,80`.
- Valores monetários serão armazenados com tipo decimal, nunca `float`, e registrados como fotografia (snapshot) na proposta para que mudanças futuras nos CSVs não alterem orçamentos já salvos.
- Datas dos datasets usarão ISO 8601 (`YYYY-MM-DD`), preços estarão em BRL e unidades serão explícitas nos schemas e respostas.
- Os CSVs serão versionados no repositório, em diretório próprio do backend, e carregados por uma camada única de catálogo.
- A seleção por menor preço só poderá ocorrer depois da aplicação de todas as regras técnicas.
- Erros de domínio devem retornar mensagens estáveis, em português, com causa e campo envolvidos.
- A proposta é um pré-dimensionamento acadêmico e não substitui projeto executivo, inspeção do local, normas, homologação da distribuidora ou responsabilidade técnica.

### 3.2 Decisões que devem ser fechadas na TASK-16

> **Decisão concluída em 2026-10-09:** as sete definições desta seção foram consolidadas no [ADR-001 — Convenções do pré-dimensionamento fotovoltaico](adr/ADR-001-decisoes-dimensionamento-fotovoltaico.md). O backlog priorizado e o estado do quadro estão em [Backlog e Kanban — Sprint 2](backlog_sprint2.md).

Antes do desenvolvimento do motor, registrar no backlog e na documentação técnica a decisão para estes pontos:

1. **Capacidade de bateria:** evitar descontar o DoD duas vezes. Adotar uma única convenção e cobri-la por teste. Sugestão:
   - `energia_autonomia = consumo_diario × autonomia_h / 24`;
   - `capacidade_nominal_requerida = energia_autonomia / (DoD × eficiencia_bateria)`;
   - `quantidade = ceil(capacidade_nominal_requerida / capacidade_nominal_unitaria)`.
2. **Eficiência da bateria:** definir se é parâmetro da simulação ou propriedade do equipamento. Como o schema atual do CSV não contém esse campo, a proposta deve persistir o valor utilizado.
3. **Arranjo de strings:** definir como distribuir módulos por string/MPPT. As validações de Voc e Vmp dependem de `modulos_por_string`, portanto não basta multiplicar sempre pelo total de módulos.
4. **Corrente de entrada:** embora o CSV contenha `Isc`, `Imp` e corrente máxima do inversor, os critérios atuais não exigem formalmente essa checagem. Decidir se ela entra nesta sprint ou fica documentada como limitação.
5. **Custos adicionais:** definir entrada explícita (itens e valores) ou percentual configurável. Não embutir silenciosamente os 25% citados em `SPEC.md` sem decisão de produto.
6. **Regra de carregamento FV mínimo do inversor:** a regra de 70% presente em `SPEC.md` não aparece nos critérios das tasks nem em `AGENTS.md`; não deve bloquear inversores nesta sprint sem aprovação e evidência técnica.
7. **Atualização de preços:** a `data_coleta` representa a fotografia comercial usada na proposta. Atualizações de catálogo ficam fora da alteração de propostas existentes.

### 3.3 Fora do escopo

- dimensionamento estrutural do telhado;
- sombreamento, azimute, inclinação e perdas horárias detalhadas;
- cálculo elétrico executivo de cabos, proteções e aterramento;
- homologação junto à concessionária;
- financiamento, payback, tarifa e retorno sobre investimento;
- atualização automática de preços via scraping;
- migração do Create React App para Vite ou adoção de Tailwind.

## 4. Estratégia de arquitetura

Separar cálculo puro, acesso a dados, persistência e HTTP para permitir testes determinísticos.

```text
Residência autenticada
        |
        v
Relatório de consumo (C_m) ---- Recurso solar (HSP + fonte)
        |                              |
        +--------------+---------------+
                       v
              Serviço de dimensionamento
                       |
          +------------+-------------+
          v                          v
 Catálogo CSV validado       Regras de compatibilidade
          |                          |
          +------------+-------------+
                       v
             Orçamento + snapshot
                       |
                       v
              Proposta persistida
                       |
                       v
             API protegida + frontend
```

Estrutura sugerida, adaptável aos padrões existentes:

```text
backend/
  alembic/                         migrations versionadas
  data/pv/                         modulos.csv, inversores.csv, baterias.csv
  app/
    models/pv.py                   entidades persistidas
    schemas/pv.py                  contratos e validações
    crud/pv.py                     acesso às propostas
    services/
      pv_catalog.py                leitura e validação dos CSVs
      solar_resource.py            resolução e validação do HSP
      pv_sizing.py                 cálculos puros
      pv_selection.py              módulos, strings e inversores
      storage_sizing.py            baterias
      pv_budget.py                 orçamento
    routers/pv.py                  endpoints protegidos
  tests/
    unit/                           fórmulas, datasets e compatibilidade
    integration/                    API, persistência e autorização
frontend/src/
  components/pv/                   configuração, comparação e proposta
  types/pv.ts                      contratos TypeScript
docs/
  fontes_fotovoltaicas.md          fontes, premissas e cenários
```

O arquivo principal da API deve apenas registrar o router; fórmulas e seleção não devem ficar dentro dos endpoints.

## 5. Modelo de persistência proposto

Criar migration versionada para a entidade principal `pv_proposals` e seus itens. A migration deve funcionar tanto em banco novo quanto sobre o SQLite atual.

### 5.1 Proposta (`pv_proposals`)

- `id`, `property_id` e `user_id` com chaves estrangeiras e índices;
- status da proposta, data de criação e atualização;
- consumo mensal de referência e data do cálculo;
- HSP, unidade, origem, data da fonte e indicação de entrada manual;
- percentual de compensação, dias do período e performance ratio;
- energia alvo, potência FV requerida e potência instalada;
- opção de bateria, autonomia, eficiência, capacidade requerida e instalada;
- custo de módulos, inversor, baterias, adicionais, equipamentos e total;
- aviso/versão da metodologia, permitindo rastrear a fórmula aplicada.

### 5.2 Itens e seleção (`pv_proposal_items`)

Persistir uma linha por item selecionado (`module`, `inverter`, `battery`, `additional`) com:

- identificador do catálogo e tipo do item;
- fabricante e modelo usados na simulação;
- quantidade, unidade, preço unitário e subtotal;
- snapshot JSON das especificações técnicas relevantes;
- para módulos, quantidade total e configuração de strings;
- para inversor, diagnósticos de compatibilidade;
- para bateria, capacidade nominal/útil e DoD utilizados.

Mesmo com `user_id` na proposta para reforçar o isolamento, toda consulta deve validar também que a residência pertence ao usuário autenticado. Exclusões da residência devem ter comportamento de cascata definido e testado.

## 6. Contrato inicial da API

Os nomes finais podem ser ajustados na TASK-29, preservando os recursos abaixo:

| Método e rota | Responsabilidade |
|---|---|
| `GET /api/pv/datasets/modules` | Listar módulos válidos e metadados do catálogo. |
| `GET /api/pv/datasets/inverters` | Listar inversores válidos. |
| `GET /api/pv/datasets/batteries` | Listar baterias válidas. |
| `POST /api/properties/{property_id}/pv/simulations` | Calcular sem persistir; retornar elegíveis, rejeições e orçamento. |
| `POST /api/properties/{property_id}/pv/proposals` | Revalidar no servidor e persistir a proposta escolhida. |
| `GET /api/properties/{property_id}/pv/proposals` | Listar propostas da residência do usuário. |
| `GET /api/properties/{property_id}/pv/proposals/{proposal_id}` | Consultar resultado completo. |
| `PUT /api/properties/{property_id}/pv/proposals/{proposal_id}` | Alterar configuração e recalcular integralmente. |
| `DELETE /api/properties/{property_id}/pv/proposals/{proposal_id}` | Excluir proposta pertencente ao usuário. |

O payload de simulação recebe apenas parâmetros controláveis (`hsp`, origem do HSP, compensação, PR, dias, escolha/opção de módulo, armazenamento, autonomia, eficiência e bateria). O consumo é derivado da residência. Respostas devem distinguir:

- erros de entrada (`422`);
- residência ou proposta não encontrada/sem acesso (`404`, sem revelar existência de recurso de outro usuário);
- ausência de consumo calculável ou de combinação compatível (`409` com diagnóstico de domínio);
- falha de catálogo no início da aplicação (`500` com log detalhado; sem disponibilizar catálogo parcialmente inválido).

## 7. Dependências e sequência de execução

### 7.1 Grafo de dependências

```text
TASK-16
  +--> TASK-17 ----------------------------------------------+
  +--> TASK-18 --+                                           |
  +--> TASK-19 --+--> TASK-21 --> TASK-24 --> TASK-25 --+     |
  +--> TASK-20 --+                 |          |         |     |
  +--> TASK-22 --> TASK-23 --------+          +--> TASK-27    |
                                   +--> TASK-26 ------+  |     |
                                                       v v     v
                                                     TASK-28
                                                        |
                          +-----------------------------+------+
                          v                                    v
                       TASK-29 ----------------------------> TASK-30
                          |                                    |
                          +--------------------------------> TASK-31
                                                               |
                 TASK-32 --------------------------------------+--> TASK-33
                                                                     |
                                                                     v
                                                                  TASK-34
```

Regras de precedência:

- TASK-21 só termina após os três CSVs existirem e serem validados.
- TASK-25 depende da quantidade de módulos e da configuração de strings, não apenas da potência calculada.
- TASK-27 depende da seleção de inversor e do resultado de armazenamento.
- TASK-28 recebe resultados já tecnicamente válidos; orçamento não corrige incompatibilidades.
- TASK-29 só expõe serviços de domínio cobertos por testes unitários.
- TASK-30 e TASK-31 podem iniciar com mocks após o contrato da API ser estabilizado, mas só terminam integradas à API real.
- TASK-33 exige persistência, API, fluxo visual e isolamento concluídos.
- TASK-34 começa junto aos datasets e é encerrada após os cenários integrados serem reproduzidos.

### 7.2 Ondas de entrega

O trabalho é organizado por dependência, sem assumir duração ou quantidade de pessoas da equipe.

| Onda | Tasks | Resultado verificável | Gate de saída |
|---|---|---|---|
| 0 — Alinhamento | TASK-16 | Épicos, US, dependências, ADRs e Kanban configurados. | Fórmulas, strings, custos e contratos acordados. |
| 1 — Fundação de dados | TASK-17, TASK-18, TASK-19, TASK-20, TASK-22 | Migration inicial, datasets rastreáveis e modelo de HSP. | Fontes revisadas; schemas e unidades congelados. |
| 2 — Catálogo e motor | TASK-21, TASK-23, TASK-24, TASK-26 | CSVs carregados e cálculos puros funcionando. | Testes unitários de limites e exemplos aprovados. |
| 3 — Compatibilidade e preço | TASK-25, TASK-27, TASK-28 | Soluções elegíveis, rejeições explicadas e BOM calculada. | Nenhuma solução incompatível pode ser orçada. |
| 4 — API e experiência | TASK-29, TASK-30, TASK-31 | Fluxo autenticado da residência à proposta. | Swagger completo e cenários manuais aprovados. |
| 5 — Qualidade e evidências | TASK-32, TASK-33, TASK-34 | Regressão, integração, segurança e documentação final. | Pipeline verde e Definition of Done atendida. |

## 8. Plano detalhado por task

| Task | Implementação planejada | Dependências | Evidência de conclusão |
|---|---|---|---|
| **TASK-16** | Criar épicos (Dados FV, Motor, Armazenamento, Proposta, Integração), cadastrar US/critério, ligar dependências, definir prioridade e registrar decisões da seção 3.2. Configurar o quadro. | Nenhuma. | Backlog revisado; Kanban com `Backlog`, `To Do`, `In Progress`, `Review`, `Done`; grafo sem dependência circular. |
| **TASK-17** | Adicionar Alembic, modelos de proposta e itens, relacionamentos com usuário/residência, snapshots técnicos e monetários, CRUD filtrado por proprietário e migrations de upgrade/downgrade. | TASK-16. | Migration aplicada em banco vazio e cópia do banco atual; teste de vínculo, cascata e isolamento. |
| **TASK-18** | Criar `modulos.csv` com no mínimo 10 produtos distintos. Separar fonte técnica do fabricante e referência comercial brasileira quando necessário, mantendo URL rastreável. | TASK-16. | Cabeçalho exato, números positivos, IDs únicos, URLs e datas verificadas. |
| **TASK-19** | Criar `inversores.csv` com no mínimo 8 itens, cobrindo on-grid e híbridos suficientes para os dois cenários. Normalizar booleano e tipo. | TASK-16. | MPPT, limites, capacidade FV, preço e fontes presentes e coerentes. |
| **TASK-20** | Criar `baterias.csv` com no mínimo 6 itens e unidades normalizadas. Conferir consistência aproximada entre V, Ah e kWh, documentando variações de datasheet. | TASK-16. | Capacidade, DoD, ciclos, tensão, preço e fontes validados. |
| **TASK-21** | Implementar leitor central com schemas tipados, validação de cabeçalho, vazio, tipos, faixas, IDs duplicados, mínimo de registros e erro `arquivo:linha:campo`. Carregar de forma atômica e disponibilizar catálogo somente se todos os arquivos forem válidos. | TASK-18, 19 e 20. | Testes com CSV válido e fixtures inválidas para cada classe de erro. |
| **TASK-22** | Permitir HSP manual positivo e preparar associação com localização da residência. Persistir valor, unidade (`kWh/m²/dia`), origem, data e modo de obtenção. Não inventar HSP quando a localização não possuir fonte configurada. | TASK-16; integra-se à 17. | UI confirma o valor; API rejeita zero/negativo; proposta preserva proveniência. |
| **TASK-23** | Implementar funções puras para `E_FV` e `P_FV`, com Decimal/precisão definida, validação de compensação, HSP, dias e PR. Expor valores de entrada e saída com unidades. | TASK-22 e consumo da Sprint 1. | Testes de exemplo, limites e divisão por zero; resultado reproduzível. |
| **TASK-24** | Selecionar módulo pelo catálogo, calcular `ceil(P_FV×1000/P_modulo)`, potência instalada e alternativas elegíveis. Não fixar potência ou preço no código. | TASK-21 e 23. | Comparação retorna fabricante, modelo, Wp, quantidade, kWp e preço de cada opção. |
| **TASK-25** | Gerar arranjo de strings explícito e validar potência FV máxima, Voc máximo e Vmp dentro do MPPT; produzir motivo estruturado para cada rejeição; ordenar compatíveis por preço somente ao final. | TASK-19, 21 e 24. | Testes isolam rejeições por potência, Voc e limites inferior/superior de Vmp. |
| **TASK-26** | Implementar caminho sem bateria com custo zero e caminho com bateria para consumo diário, autonomia, capacidade nominal requerida, quantidade arredondada e capacidade instalada. | TASK-20, 21 e 23; decisão 3.2.1. | Testes de 0 h, limites válidos, DoD/eficiência inválidos e arredondamento. |
| **TASK-27** | Filtrar inversores por `compativel_bateria` quando armazenamento estiver ativo e bloquear combinações inválidas com explicação visível. Manter inversores on-grid no cenário sem bateria. | TASK-25 e 26. | Testes das duas arquiteturas e erro de tentativa de orçamento incompatível. |
| **TASK-28** | Montar BOM imutável com quantidades, preço unitário, subtotal, categorias, adicionais, custo de equipamentos e total. Conferir somas no servidor. | TASK-24, 25, 26 e 27. | Testes monetários sem bateria, com bateria, adicionais e arredondamento em BRL. |
| **TASK-29** | Criar router e schemas de API para catálogos, simulação e CRUD de propostas. Derivar consumo da residência autenticada, centralizar autorização, documentar exemplos e erros no OpenAPI. | TASK-17, 21 a 28. | Swagger testado; respostas incluem cálculo, seleção, rejeições e orçamento; testes de 401/404/422/409. |
| **TASK-30** | Adicionar ação `Dimensionar sistema solar` na residência, buscar consumo, coletar/confirmar HSP, compensação, PR e bateria, exibir validações por campo e estados de carregamento/vazio/erro. | Contrato da TASK-29; pode iniciar com mock. | Fluxo parte da residência correta e nunca pede ao usuário para redigitar `C_m`. |
| **TASK-31** | Criar resumo técnico, cards dos componentes, configuração de strings, armazenamento, geração estimada, BOM e total; incluir aviso acadêmico permanente. Permitir voltar e recalcular. | TASK-28, 29 e 30. | Cenários com e sem bateria renderizados e persistidos com unidades e valores consistentes. |
| **TASK-32** | Consolidar suíte unitária para catálogo, fórmulas, seleção, compatibilidade e orçamento; usar fixtures pequenas e determinísticas, independentes dos preços reais. | Implementada incrementalmente nas TASK-21 a 28. | Todos os limites dos critérios cobertos; suíte reproduzível e sem acesso à rede. |
| **TASK-33** | Criar testes de API ponta a ponta: dois usuários, residência, equipamentos, consumo, proposta sem bateria, proposta com bateria, persistência e tentativas de acesso cruzado. | TASK-17, 29, 30, 31 e 32. | Testes provam resultados, orçamento e isolamento em leitura, alteração e exclusão. |
| **TASK-34** | Manter documentação viva de fontes, datas, PR, HSP, DoD, eficiência, metodologia e limitações. Registrar inputs/outputs dos dois cenários reproduzíveis e comandos de execução. | Inicia com TASK-18; termina após TASK-33. | URLs auditáveis, cenários reproduzidos e números conferidos contra testes. |

## 9. Estratégia de testes e validação

### 9.1 Pirâmide de testes

1. **Testes unitários de domínio**
   - fórmulas com valores conhecidos;
   - arredondamentos (`ceil`) e precisão monetária;
   - limites e entradas inválidas;
   - seleção e motivos de incompatibilidade;
   - caminho sem bateria e com bateria.
2. **Testes de dataset**
   - cabeçalhos e contagens mínimas;
   - linha vazia, campo vazio, ID duplicado e tipo incorreto;
   - URLs/datas válidas e números não negativos;
   - consistência das faixas MPPT e valores elétricos.
3. **Testes de API/persistência**
   - autenticação obrigatória;
   - consumo derivado da residência;
   - CRUD de proposta e snapshot de preço;
   - proteção contra acesso de outro usuário;
   - respostas de erro e OpenAPI.
4. **Testes de frontend**
   - formulário e mensagens por campo;
   - estados de loading, erro e ausência de solução;
   - renderização das duas propostas;
   - aviso acadêmico e totais.
5. **Teste de aceitação reproduzível**
   - executar um cenário on-grid sem bateria;
   - executar um cenário híbrido com bateria;
   - comparar resultados da UI, API, banco e documentação.

### 9.2 Casos de borda obrigatórios

- residência sem equipamentos ou consumo total igual a zero;
- HSP igual a zero, negativo ou ausente;
- compensação fora do intervalo aprovado;
- PR, DoD ou eficiência iguais a zero ou acima de 100%;
- autonomia negativa ou acima de 24 horas;
- quantidade fracionária que exige arredondamento para cima;
- nenhum inversor compatível por potência, Voc ou Vmp;
- bateria solicitada com apenas inversor on-grid selecionado;
- CSV parcialmente válido, duplicado ou abaixo da quantidade mínima;
- alteração do CSV após a criação de uma proposta;
- tentativa de consultar/alterar/excluir proposta de outro usuário.

### 9.3 Comandos de verificação previstos

Os comandos devem ser normalizados durante a sprint e registrados no README. Base inicial:

```bash
cd backend
python -m unittest discover -s tests -v
alembic upgrade head
alembic downgrade -1

cd ../frontend
npm test -- --watchAll=false
npm run build
```

## 10. Gestão do trabalho no Kanban

O quadro versionado, com épicos, user stories, prioridades, dependências e estado das tasks, está em [Backlog e Kanban — Sprint 2](backlog_sprint2.md).

### 10.1 Política das colunas

- **Backlog:** item documentado, ainda não refinado ou fora do compromisso imediato.
- **To Do:** critérios claros, dependências concluídas, fontes/contratos disponíveis e tamanho aceitável.
- **In Progress:** implementação ativa; limitar trabalho em progresso para reduzir integrações tardias.
- **Review:** pull request aberto, testes executados, evidências anexadas e revisão técnica/funcional pendente.
- **Done:** critérios de aceite, testes, documentação e integração concluídos na branch principal.

### 10.2 Definition of Ready

Uma task só entra em `To Do` quando:

- objetivo e critérios de aceite estão claros;
- dependências estão concluídas ou possuem contrato estável;
- entradas, saídas, unidades e mensagens de erro foram definidas;
- fonte dos dados ou fixture de teste está disponível;
- não existe decisão de produto/técnica bloqueadora em aberto.

### 10.3 Definition of Done da Sprint 2

A sprint só pode ser considerada concluída quando:

- todas as TASK-16 a TASK-34 estão em `Done` ou uma mudança de escopo foi formalmente registrada;
- os três datasets atingem as contagens mínimas, schemas e rastreabilidade exigidos;
- migrations funcionam sobre banco vazio e banco existente;
- cálculos e compatibilidades são realizados no backend e cobertos por testes;
- nenhuma proposta tecnicamente incompatível pode ser salva ou orçada;
- API e UI executam os cenários com e sem bateria;
- isolamento por usuário é comprovado por teste automatizado;
- Swagger, README e evidências técnicas estão atualizados;
- testes do backend, testes do frontend e build de produção passam;
- a proposta exibe claramente a natureza acadêmica e preliminar do resultado.

## 11. Estratégia de integração e revisão

- Entregar mudanças pequenas por task ou conjunto coeso, evitando uma única integração ao final.
- Para cada PR, relacionar a task, listar critérios atendidos, migrations, testes executados e capturas/evidências quando houver UI.
- Alterações de schema de CSV exigem atualização conjunta do validador, fixtures, documentação e tipos de resposta.
- Alterações de fórmula exigem atualização conjunta do ADR, implementação, testes e cenário reproduzível.
- Antes de integrar TASK-30/31, validar o contrato OpenAPI da TASK-29 para evitar duplicação de regras no frontend.
- Não permitir cálculo técnico apenas no cliente; o frontend pode apresentar prévias, mas a API recalcula antes de persistir.

## 12. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Fonte comercial não contém todos os dados técnicos. | Registro incompleto ou não rastreável. | Combinar datasheet oficial para especificações e fornecedor brasileiro para preço, documentando ambas as referências. |
| Links e preços mudam ao longo da sprint. | Evidência deixa de ser reproduzível. | Persistir data de coleta, salvar snapshot na proposta e revisar URLs antes do encerramento. |
| Fórmula de bateria aplica DoD duas vezes. | Superdimensionamento e custo incorreto. | Fechar convenção na TASK-16 e usar testes numéricos independentes. |
| Voc/Vmp validados contra total de módulos, sem strings. | Inversores rejeitados ou aceitos incorretamente. | Modelar `modulos_por_string`, quantidade de strings e MPPT antes da TASK-25. |
| `create_all` não evolui bancos existentes. | Aplicação falha em instalações já usadas. | Introduzir Alembic na TASK-17 e testar upgrade sobre cópia do SQLite atual. |
| Regras duplicadas no frontend e backend. | Resultados divergentes. | Backend como fonte de verdade; frontend apenas coleta dados e exibe respostas. |
| Testes dependem dos preços reais do CSV. | Suíte instável após atualização de catálogo. | Fixtures mínimas e determinísticas para unidade; CSV real validado em suíte separada. |
| Escopo visual ou de stack cresce durante a sprint. | Atraso nas funções críticas. | Reutilizar CSS/componentes atuais e manter migrações de stack fora do escopo. |
| Falta de inversor compatível para um cenário de teste. | Fluxo integrado bloqueado. | Planejar cobertura de faixas e arquiteturas ao montar TASK-19, sem falsificar dados. |

## 13. Marcos de aceite

### Marco A — Fundação pronta

- backlog e decisões fechados;
- migrations aplicáveis;
- datasets completos e aprovados;
- HSP com proveniência definida.

### Marco B — Motor técnico pronto

- cálculo FV e armazenamento aprovados;
- seleção de módulos e inversores reproduzível;
- incompatibilidades explicadas;
- orçamento consistente e sem itens inválidos.

### Marco C — Fluxo de produto pronto

- endpoints protegidos e documentados;
- usuário inicia pela residência e utiliza o consumo já calculado;
- proposta completa é exibida, salva e recuperada.

### Marco D — Sprint finalizada

- cenários com e sem bateria aprovados;
- isolamento entre usuários comprovado;
- regressão e build verdes;
- fontes, premissas, limitações e resultados reproduzíveis documentados.

## 14. Resultado esperado

Ao fim da Sprint 2, um usuário autenticado deverá selecionar uma residência própria com consumo calculado, informar ou confirmar os parâmetros solares, simular alternativas reais de equipamentos, compreender eventuais incompatibilidades, escolher uma solução válida e salvar uma proposta preliminar detalhada. A mesma proposta deverá poder ser consultada posteriormente sem sofrer alteração caso os preços dos datasets sejam atualizados.
