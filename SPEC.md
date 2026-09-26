# SPEC.MD — ESPECIFICAÇÕES TÉCNICAS E ARQUITETURA DO SISTEMA

## 1. Arquitetura Geral e Stack Tecnológica
O sistema é estruturado na arquitetura Decoupled/Client-Server para execução 100% local.

- **Frontend:** React 18+ (Vite), Tailwind CSS (Tema Dark/Cyan), Lucide React (ícones), Recharts (gráficos), Axios.
- **Backend:** Python 3.10+ (FastAPI), Pydantic (validação de schemas), Pandas (manipulação dos datasets CSV), SQLite/SQLAlchemy (persistência de imóveis e usuários).
- **Comunicação:** REST API com JSON.
- **Execução:** Servidores locais (`uvicorn main:app --reload` na porta 8000 e `npm run dev` na porta 5173).

---

## 2. Padrão Visual e Tema UI (Dark & Cyan)
- **Fundo Primário (Dark):** `#0a0f1d` (Slate/Zinc ultra escuro)
- **Superfícies/Cards:** `#111827` / `#1f293d`
- **Cor Primária/Destaque (Cyan):** `#06b6d4` (Cyan-500) / `#22d3ee` (Cyan-400)
- **Texto:** `#f8fafc` (Slate-50) para títulos, `#94a3b8` (Slate-400) para legendas.
- **Bordas e Dividers:** `border-cyan-500/20` ou `border-slate-800`.
- **Estilo de Componentes:** Bordas arredondadas (`rounded-xl`), efeitos de brilho suave (`shadow-cyan-500/10`), tipografia moderna (Inter ou Outfit).

---

## 3. Schemas dos Datasets (CSV)

### 3.1 `modulos.csv` (Mínimo 10 registros reais)
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | String | Identificador único (ex: `FV001`) |
| `fabricante` | String | Marca do painel |
| `modelo` | String | Código do modelo |
| `potencia_wp` | Float | Potência nominal em Wp |
| `voc_v` | Float | Tensão de circuito aberto (V) |
| `isc_a` | Float | Corrente de curto-circuito (A) |
| `vmp_v` | Float | Tensão de máxima potência (V) |
| `imp_a` | Float | Corrente de máxima potência (A) |
| `eficiencia_pct` | Float | Eficiência em % |
| `preco_brl` | Float | Preço unitário em R$ |
| `fornecedor` | String | Fornecedor de referência |
| `data_coleta` | Date | Data no formato YYYY-MM-DD |
| `url_fonte` | String | Link da fonte real |

### 3.2 `inversores.csv` (Mínimo 8 registros reais)
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | String | Identificador único (ex: `INV001`) |
| `fabricante` | String | Marca do inversor |
| `modelo` | String | Código do modelo |
| `tipo` | String | On-Grid, Off-Grid ou Híbrido |
| `potencia_nominal_w` | Float | Potência contínua de saída (W) |
| `potencia_max_fv_w` | Float | Potência máxima fotovoltaica suportada (W) |
| `tensao_max_entrada_v` | Float | Tensão máxima CC suportada (V) |
| `faixa_mppt_min_v` | Float | Tensão mínima da faixa MPPT (V) |
| `faixa_mppt_max_v` | Float | Tensão máxima da faixa MPPT (V) |
| `corrente_max_entrada_a`| Float | Corrente máxima por MPPT (A) |
| `numero_mppt` | Integer | Quantidade de rastreadores MPPT |
| `compativel_bateria` | Boolean | `True` se aceita baterias, senão `False` |
| `preco_brl` | Float | Preço unitário em R$ |
| `fornecedor` | String | Nome do distribuidor/loja |
| `data_coleta` | Date | Data da pesquisa |
| `url_fonte` | String | Link da fonte de dados |

### 3.3 `baterias.csv` (Mínimo 6 registros reais)
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | String | Identificador único (ex: `BAT001`) |
| `fabricante` | String | Marca da bateria |
| `modelo` | String | Modelo |
| `tecnologia` | String | Química (ex: LiFePO4, Chumbo-Ácido) |
| `tensao_nominal_v` | Float | Tensão nominal (V) |
| `capacidade_ah` | Float | Capacidade em Ampére-hora (Ah) |
| `capacidade_kwh` | Float | Capacidade de energia nominal (kWh) |
| `dod_pct` | Float | Profundidade de descarga recomendada (%) |
| `ciclos` | Integer | Vida útil em ciclos estimados |
| `preco_brl` | Float | Preço unitário em R$ |
| `fornecedor` | String | Nome do fornecedor |
| `data_coleta` | Date | Data da coleta |
| `url_fonte` | String | URL da especificação/loja |

---

## 4. Regras de Negócio e Fórmulas Matemáticas

### 4.1 Consumo Energético Mensal Residencial
Para cada equipamento $i$:
$$E_{eq,i} = \frac{P_i \times Q_i \times H_i \times 30}{1000} \quad [\text{kWh/mês}]$$
Consumo Total da Residência:
$$C_m = \sum_{i=1}^{n} E_{eq,i} \quad [\text{kWh/mês}]$$

### 4.2 Dimensionamento Fotovoltaico
1. **Energia Mensal Alvo ($E_{FV}$):**
   $$E_{FV} = C_m \times f$$
   *onde $f$ é a fração de atendimento do consumo (ex: 1.0 para 100%).*

2. **Potência Fotovoltaica Necessária ($P_{FV}$):**
   $$P_{FV} = \frac{E_{FV}}{\text{HSP} \times D \times \eta} \quad [\text{kWp}]$$
   *Padrões adote: $D = 30$ dias, $\eta = 0.75$ a $0.80$ (Performance Ratio).*

3. **Quantidade de Módulos ($N$):**
   $$N = \left\lceil \frac{P_{FV} \times 1000}{P_{\text{módulo}}} \right\rceil$$

4. **Potência Efetivamente Instalada ($P_{\text{instalada}}$):**
   $$P_{\text{instalada}} = \frac{N \times P_{\text{módulo}}}{1000} \quad [\text{kWp}]$$

### 4.3 Dimensionamento do Armazenamento (Baterias)
1. **Consumo Diário Médio ($E_d$):**
   $$E_d = \frac{C_m}{30} \quad [\text{kWh/dia}]$$

2. **Energia para Autonomia Solicitada ($E_{\text{autonomia}}$):**
   $$E_{\text{autonomia}} = E_d \times \left( \frac{A}{24} \right) \quad [\text{kWh}]$$
   *onde $A$ é a autonomia em horas.*

3. **Capacidade Necessária ($C_{\text{bat}}$):**
   $$C_{\text{bat}} = \frac{E_{\text{autonomia}}}{\text{DoD} \times \eta_{\text{bat}}} \quad [\text{kWh}]$$

4. **Quantidade de Baterias ($N_{\text{bat}}$):**
   $$C_{\text{útil}} = C_{\text{nominal}} \times \text{DoD}$$
   $$N_{\text{bat}} = \left\lceil \frac{C_{\text{bat}}}{C_{\text{útil}}} \right\rceil$$

### 4.4 Filtro e Validação do Inversor
Um inversor é considerado **compatível** se e somente se:
1. $P_{\text{instalada}} \times 1000 \le \text{potencia\_max\_fv\_w}$
2. $P_{\text{instalada}} \times 1000 \ge \text{potencia\_nominal\_w} \times 0.7$
3. Se Baterias ativas $\rightarrow \text{compativel\_bateria} == \text{True}$.

### 4.5 Formação do Orçamento
$$C_{\text{equipamentos}} = (N \times \text{Preço}_{\text{módulo}}) + \text{Preço}_{\text{inversor}} + (N_{\text{bat}} \times \text{Preço}_{\text{bateria}})$$
$$C_{\text{adicionais}} = C_{\text{equipamentos}} \times 0.25 \quad (\text{Estruturas, cabeamento, proteções e instalação estimados})$$
$$\text{Custo Total Estimado} = C_{\text{equipamentos}} + C_{\text{adicionais}}$$

---

## 5. Endpoints Principais da API (Python/FastAPI)

- `GET /api/equipamentos/catalogo`: Retorna o catálogo de eletrodomésticos básicos.
- `POST /api/consumo/calcular`: Recebe lista de aparelhos e retorna o $C_m$ total.
- `GET /api/datasets/modulos`: Lista módulos solares disponíveis.
- `GET /api/datasets/inversores`: Lista inversores disponíveis.
- `GET /api/datasets/baterias`: Lista baterias disponíveis.
- `POST /api/dimensionamento/processar`:
  - **Input JSON:** `consumo_kwh_mes`, `hsp`, `fator_atendimento`, `modulo_id`, `inversor_id`, `usar_bateria` (bool), `horas_autonomia`, `bateria_id`.
  - **Output JSON:** Resumo técnico completo com potências, quantidades, diagnósticos de compatibilidade e orçamento detalhado.