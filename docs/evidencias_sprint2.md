# Evidências reproduzíveis — Sprint 2

Este documento encerra a TASK-34 e registra as premissas, a metodologia, as
fontes e dois cenários de aceite do pré-dimensionamento fotovoltaico. Os valores
abaixo foram reproduzidos em **2026-10-10** com a versão `ADR-001/v1` e com os
CSVs versionados em `backend/data/pv/`.

> O resultado é um pré-dimensionamento acadêmico. Ele não substitui projeto
> executivo, vistoria, homologação junto à distribuidora ou responsabilidade
> técnica. Preços não incluem frete, tributos, estruturas e serviços que não
> apareçam explicitamente na BOM.

## Rastreabilidade dos dados

Cada registro dos catálogos contém fabricante, modelo, fornecedor, data de
coleta e URL técnica. A referência comercial usada no preço é mantida nos
documentos abaixo:

- [módulos fotovoltaicos](fontes_modulos_fotovoltaicos.md): 10 produtos, preços
  coletados em 2026-10-09 e uma referência atualizada em 2026-10-10;
- [inversores fotovoltaicos](fontes_inversores_fotovoltaicos.md): 8 produtos,
  preços coletados em 2026-10-09;
- [baterias fotovoltaicas](fontes_baterias_fotovoltaicas.md): 6 produtos,
  preços coletados em 2026-10-09 e duas referências coletadas em 2026-10-10.

As URLs técnicas ficam também em `url_fonte` nos CSVs e são copiadas para o
snapshot imutável da proposta. Alterar um CSV afeta apenas novas simulações.

## Premissas e metodologia

| Parâmetro | Convenção usada |
|---|---|
| Consumo de referência (`C_m`) | Derivado dos equipamentos da residência autenticada; não é aceito do cliente na simulação. |
| HSP | Entrada manual positiva, em `kWh/m²/dia`, acompanhada de origem e data. O sistema não inventa um valor a partir da localização. |
| Compensação (`f`) | Fração no intervalo `(0, 1]`. |
| Performance ratio (`PR`) | Fração no intervalo `(0, 1]`; nos cenários: `0,80`. |
| Período (`D`) | Inteiro positivo; nos cenários: 30 dias. |
| Eficiência da bateria | Parâmetro da simulação no intervalo `(0, 1]`; padrão e valor dos cenários: `0,95`. |
| DoD | Lido da bateria escolhida. Para a Dyness B4850: `90%`. |
| Dinheiro | `Decimal`, BRL, arredondamento para duas casas com `ROUND_HALF_UP`. |

As fórmulas aplicadas são:

```text
E_FV = C_m × f
P_FV = E_FV / (HSP × D × PR)
N_módulos = ceil(P_FV × 1000 / potência_módulo)

E_diária = C_m / D
E_autonomia = E_diária × autonomia_h / 24
C_nominal_requerida = E_autonomia / (DoD × eficiência_bateria)
N_baterias = ceil(C_nominal_requerida / capacidade_nominal_unitária)
```

O DoD é aplicado uma única vez. Cada string é verificada individualmente
contra Voc máximo e faixa MPPT do inversor. A potência instalada total deve ser
menor ou igual à potência FV máxima. Com autonomia positiva, somente inversor
compatível com bateria é elegível. A especificação normativa completa está no
[ADR-001](adr/ADR-001-decisoes-dimensionamento-fotovoltaico.md).

## Cenário A — on-grid sem bateria

### Entradas

| Campo | Valor |
|---|---:|
| Consumo mensal derivado | 300 kWh/mês |
| HSP manual | 5 kWh/m²/dia |
| Origem/data do HSP | `Entrada manual reproduzível da TASK-34` / 2026-10-10 |
| Compensação | 100% (`1,00`) |
| PR | 80% (`0,80`) |
| Período | 30 dias |
| Autonomia | 0 h |
| Módulo | `MOD-CAN-550-001` |
| Inversor | `INV-GRO-2500-001` |

### Saídas conferidas

| Resultado | Valor |
|---|---:|
| Energia-alvo | 300,000 kWh/mês |
| Potência FV requerida | 2,500000 kWp |
| Módulos Canadian Solar CS6W-550MS | 5 × 550 Wp |
| Potência instalada | 2,750000 kWp |
| Arranjo | MPPT 1: 5 módulos; Voc 248,000 V; Vmp 208,500 V |
| Custo dos módulos | R$ 2.945,00 |
| Inversor Growatt MIN 2500TL-X | R$ 2.899,00 |
| Baterias | 0; R$ 0,00 |
| **Total** | **R$ 5.844,00** |

## Cenário B — híbrido com bateria

São mantidas as entradas FV do cenário A e acrescentados:

| Campo | Valor |
|---|---:|
| Autonomia | 12 h |
| Eficiência da bateria | 95% (`0,95`) |
| Bateria | `BAT-DYN-B4850-001` — 2,4 kWh nominais, DoD 90% |
| Inversor | `INV-DEY-5000-001` |
| Custo adicional explícito | Instalação: R$ 1.500,00 |

### Saídas conferidas

| Resultado | Valor |
|---|---:|
| Consumo diário | 10,000 kWh/dia |
| Energia para autonomia | 5,000 kWh |
| Capacidade nominal requerida | 5,848 kWh |
| Baterias Dyness B4850 | 3 × 2,4 kWh |
| Capacidade nominal instalada | 7,200 kWh |
| Energia entregável instalada | 6,156 kWh |
| Módulos | 5 × 550 Wp; R$ 2.945,00 |
| Inversor híbrido Deye SUN-5K-SG01LP1-US | R$ 15.912,90 |
| Baterias | R$ 26.924,34 |
| Equipamentos | R$ 45.782,24 |
| Instalação | R$ 1.500,00 |
| **Total** | **R$ 47.282,24** |

A energia entregável instalada (`6,156 kWh`) é maior que a energia de autonomia
(`5,000 kWh`), atendendo à invariante do ADR. Os inversores on-grid são
rejeitados nesse cenário por incompatibilidade com armazenamento.

## Como reproduzir

A partir da raiz do repositório, com as dependências instaladas:

```bash
cd backend
cp .env.example .env
# Substitua SECRET_KEY no .env antes de iniciar a aplicação.
python3 -m unittest tests.test_task34_documentation_scenarios -v
python3 -m unittest tests.test_task33_pv_api_e2e -v
python3 -m unittest discover -s tests -v

cd ../frontend
npm test -- --watchAll=false
npm run build
```

O primeiro comando confere numericamente os dois cenários deste documento com
os catálogos reais. O segundo reproduz o fluxo HTTP completo, incluindo dois
usuários, consumo derivado, persistência das duas propostas e bloqueio de
leitura, alteração e exclusão cruzadas. A suíte completa valida datasets,
fórmulas, limites, snapshots e CRUD.

Para validar migrations sobre o banco configurado:

```bash
cd backend
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

## Limitações conhecidas

- HSP é manual enquanto não houver provedor confiável configurado por localização.
- Não há cálculo de sombreamento, orientação, inclinação, temperatura, perdas por cabo ou degradação específica do local.
- Corrente de entrada é informativa nesta sprint; o schema não separa limites por MPPT/entrada, conforme o ADR-001.
- Há no máximo uma string por MPPT; strings paralelas no mesmo MPPT estão fora do escopo.
- Não são dimensionados cabos, proteções, estrutura, aterramento nem adequações civis.
- Preços são fotografias de 2026-10-09, podem mudar e exigem confirmação comercial.
- Ciclos de bateria não são diretamente comparáveis sem considerar condições de ensaio e garantia.
- O resultado não confirma regras da distribuidora, normas aplicáveis ao endereço ou viabilidade de instalação.

