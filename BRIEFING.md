# BRIEFING DO PROJETO — SIMULADOR & DIMENSIONAMENTO ENERGÉTICO E FOTOVOLTAICO RESIDENCIAL

## 1. Visão Geral do Projeto
O **Sistema de Dimensionamento Energético e Fotovoltaico Residencial** é uma evolução do módulo de cálculo de consumo de energia para imóveis. O sistema permite ao cliente:
1. Cadastrar seu imóvel e estimar o consumo mensal de energia em kWh/mês com base na rotina de uso de aparelhos eletrodomésticos.
2. Realizar o **pré-dimensionamento de um sistema de geração fotovoltaica** (com opção de armazenamento por baterias/Off-Grid/Híbrido) capaz de suprir total ou parcialmente sua demanda.
3. Obter uma **proposta de orçamento preliminar**, calculada a partir de bancos de dados reais (`modulos.csv`, `inversores.csv`, `baterias.csv`) comercializados no Brasil.

---

## 2. Objetivos Principais
- **Garantir a evolução contínua:** Integrar de forma fluida a estimativa de consumo energético (etapa MVP) ao novo fluxo de dimensionamento solar e orçamento.
- **Precisão e Rastreabilidade Técnica:** Utilizar fórmulas consagradas de engenharia solar (HSP, fator de desempenho, profundidade de descarga DoD, cálculo de strings e compatibilidade MPPT).
- **Dados Reais de Mercado:** Garantir que todos os equipamentos sugeridos e orçados pertençam aos datasets validados contendo produtos comercializados no Brasil.
- **Experiência de Usuário Moderna (UI Clean Dark/Cyan):** Prover uma interface com modo escuro (`#0a0f1d`, `#111827`) e destaques em Ciano (`#06b6d4` / `#22d3ee`), fluida, reativa e de fácil compreensão.
- **Execução Local:** Garantir que o sistema rode localmente com infraestrutura simples (Backend Python + Frontend React).

---

## 3. Escopo do Sistema & Funcionalidades

### 3.1 Módulo 1 — Perfil e Consumo Energético (Aproveitado)
- Cadastro de Usuário e Autenticação.
- Gestão de Imóveis (criação, edição e exclusão de residências).
- Catálogo de Aparelhos e Padrão de Uso (quantidade x horas diárias x potência W).
- Cálculo automatizado de consumo mensal ($C_m$) em kWh/mês e gráfico de distribuição de consumo.

### 3.2 Módulo 2 — Dimensionamento Fotovoltaico
- Entrada da localização e índice de Radiação Solar / **Horas de Sol Pleno (HSP)**.
- Definição do **percentual de atendimento** ($f$) desejado (ex: 80%, 100%).
- Definição do Fator Global de Desempenho ($\eta$) / Performance Ratio (PR).
- Cálculo da **Energia Mensal Desejada ($E_{FV}$)** e da **Potência Fotovoltaica Necessária ($P_{FV}$ em kWp)**.
- Seleção e dimensionamento de Módulos Solares via `modulos.csv` (quantidade $N$ e potência efetivamente instalada $P_{instalada}$).

### 3.3 Módulo 3 — Compatibilidade & Seleção do Inversor
- Filtragem automática e recomendação de Inversores via `inversores.csv`.
- Verificação rigorosa de compatibilidade técnica:
  - Potência do arranjo FV vs. Potência Max FV Aceita pelo Inversor.
  - Janela de tensão MPPT ($V_{min}$ a $V_{max}$).
  - Limite de corrente de entrada ($I_{max}$).
  - Suporte a baterias (caso o usuário ative armazenamento).

### 3.4 Módulo 4 — Armazenamento por Baterias (Opcional)
- Toggle de ativação para Sistema com Armazenamento (Híbrido/Off-Grid).
- Definição das **Horas de Autonomia ($A$)** desejadas.
- Cálculo da capacidade útil e nominal necessária considerando Profundidade de Descarga ($\text{DoD}$) e eficiência da bateria ($\eta_{bat}$).
- Seleção de Baterias via `baterias.csv` (quantidade $N_{bat}$ e capacidade nominal/instalada em kWh).

### 3.5 Módulo 5 — Formação do Orçamento e Proposta Final
- Consolidação do custo de equipamentos ($C_{módulos} + C_{inversor} + C_{baterias}$).
- Estimativa de custos adicionais (estruturas de fixação, cabeamento, proteções e instalação).
- Apresentação de resumo claro da proposta comercial/técnica para exportação ou visualização.

---

## 4. Entregáveis do Projeto
1. **Código Fonte Completo:** Repositório local com backend Python (FastAPI/Flask) e frontend React (Vite + Tailwind CSS).
2. **Datasets Estruturados:** `modulos.csv`, `inversores.csv` e `baterias.csv` preenchidos com produtos reais.
3. **Documentação Acadêmica e Técnica:** `BRIEFING.md`, `SPEC.md`, `AGENTS.md` e registros de testes com e sem baterias.

---

## 5. Equipe Responsável
- Guilherme Vinciguerra Carvalho — RM: 571951
- Marcos Peterson Martins Pereira — RM: 573857
- Matheus Jorge Santana — RM: 574166