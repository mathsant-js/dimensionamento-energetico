# AGENTS.md — Photovoltaic System Sizing & Energy Estimation Agent Specification

## 1. Overview
This project extends the **Residential Energy Consumption Estimation System** by introducing an automated photovoltaic (PV) sizing, equipment selection, and budgeting agent framework. 

The primary goal is to take a property's reference energy consumption ($C_m$, in kWh/month), local solar radiation data (Peak Sun Hours - $HSP$), target offset percentage ($f$), and storage requirements to automatically size, validate, and price a complete solar PV solution using structured datasets.

---

## 2. Core Workflows & Formulas

### 2.1 PV Generation Sizing
1. **Target Energy Generation ($E_{PV}$)**:
   $$E_{PV} = C_m \times f$$
   *Where $C_m$ is monthly reference consumption (kWh/month) and $f$ is the target fraction/percentage to offset.*

2. **Required PV Power ($P_{PV}$)**:
   $$P_{PV} = \frac{E_{PV}}{HSP \times D \times \eta}$$
   *Where $HSP$ is daily Peak Sun Hours, $D$ is days in month (standard: 30), and $\eta$ is overall system performance ratio (PR).*

3. **Module Sizing ($N_{modules}$)**:
   $$N = \left\lceil \frac{P_{PV} \times 1000}{P_{module}} \right\rceil$$
   $$P_{installed} = \frac{N \times P_{module}}{1000} \text{ (kWp)}$$

### 2.2 Optional Battery Energy Storage System (BESS)
1. **Daily Consumption ($E_d$)**:
   $$E_d = \frac{C_m}{30}$$

2. **Autonomy Energy Required ($E_{autonomy}$)**:
   $$E_{autonomy} = E_d \times \left(\frac{A}{24}\right)$$
   *Where $A$ is required autonomy hours.*

3. **Required Battery Capacity ($C_{bat}$)**:
   $$C_{bat} = \frac{E_{autonomy}}{DoD \times \eta_{bat}}$$
   *Where $DoD$ is Depth of Discharge (percentage) and $\eta_{bat}$ is battery efficiency.*

4. **Battery Unit Sizing ($N_{bat}$)**:
   $$C_{usable} = C_{nominal} \times DoD$$
   $$N_{bat} = \left\lceil \frac{C_{required}}{C_{usable}} \right\rceil$$

### 2.3 Financial Calculation
$$\text{Total Cost} = C_{modules} + C_{inverter} + C_{batteries} + C_{additional}$$

---

## 3. Dataset Schemas & Minimum Requirements

All technical parameters must be traceable to manufacturer datasheets, and prices must reflect real market suppliers in Brazil (BRL).

### 3.1 PV Modules (`modulos.csv`)
* **Minimum count**: 10 distinct modules
* **Schema**:
  `id, fabricante, modelo, potencia_wp, voc_v, isc_a, vmp_v, imp_a, eficiencia_pct, preco_brl, fornecedor, data_coleta, url_fonte`

### 3.2 Inverters (`inversores.csv`)
* **Minimum count**: 8 distinct inverters
* **Schema**:
  `id, fabricante, modelo, tipo, potencia_nominal_w, potencia_max_fv_w, tensao_max_entrada_v, faixa_mppt_min_v, faixa_mppt_max_v, corrente_max_entrada_a, numero_mppt, compativel_bateria, preco_brl, fornecedor, data_coleta, url_fonte`

### 3.3 Batteries (`baterias.csv`)
* **Minimum count**: 6 distinct batteries
* **Schema**:
  `id, fabricante, modelo, tecnologia, tensao_nominal_v, capacidade_ah, capacidade_kwh, dod_pct, ciclos, preco_brl, fornecedor, data_coleta, url_fonte`

---

## 4. Technical Validation Rules

When executing component selection, agents must strictly enforce the following compatibility checks:

1. **Inverter PV Capacity**: $P_{installed\_W} \le \text{potencia\_max\_fv\_w}$
2. **Inverter Voltage Limits**: String $V_{oc} \le \text{tensao\_max\_entrada\_v}$
3. **Inverter MPPT Voltage Operating Range**: String $V_{mp} \ge \text{faixa\_mppt\_min\_v}$ and $V_{mp} \le \text{faixa\_mppt\_max\_v}$
4. **Storage Compatibility**: If batteries are requested ($A > 0$), $\text{compativel\_bateria}$ must be `true` (or a hybrid inverter must be selected).
5. **Data Sanitization**: No negative values, daily usage between 0 and 24 hours, non-empty required fields.

---

## 5. Agent Architecture & Execution Flow

```
[Property Registration & Historic Load Profile]
                        │
                        ▼
           [Reference Consumption (C_m)]
                        │
                        ▼
             [Solar Resource (HSP)]
                        │
                        ▼
         [Photovoltaic Sizing Engine]
                        │
                        ▼
     [Equipment Matching & Verification]
                        │
       ┌────────────────┴────────────────┐
       ▼                                 ▼
[On-Grid Sizing]            [Optional Battery Storage]
       └────────────────┬────────────────┘
                        │
                        ▼
              [Budget Generation]
                        │
                        ▼
          [Preliminary Client Proposal]
```

---

## 6. Project Backlog & Sprint Scope

### Primary MVP User Stories (Sprint 1 Priority)
* **PB01 — Account Creation**: User authentication and input validation.
* **PB02 — Login**: Secure credential verification.
* **PB03 — Property Registration**: Register housing details and location.
* **PB05 — Equipment Catalog**: View pre-populated appliances catalog with power (W).
* **PB06 — Equipment Binding**: Assign appliances to specific property.
* **PB07 — Usage Input**: Input quantity and daily hours of operation (0-24h).
* **PB09 — Individual Consumption**: Calculate equipment $kWh/month = \frac{P \times Q \times Hours \times 30}{1000}$.
* **PB10 — Total Consumption**: Aggregate total monthly kWh/month.
* **PB11 — Result Summary**: Comprehensive energy footprint summary.
* **PB14 — Validation**: Enforce boundary checks on invalid data inputs.
* **PB15 — Security & Persistence**: Data isolation per user and persistent storage.

### Secondary Scope (Photovoltaic Sizing Evolution)
* **US-PV01 — PV Dataset Creation**: Build validated datasets for modules (min 10), inverters (min 8), and batteries (min 6).
* **US-PV02 — Solar Sizing Engine**: Calculate $P_{PV}$, required panel count ($N$), and nominal installed power.
* **US-PV03 — Equipment Selector**: Match inverters based on technical bounds and pricing.
* **US-PV04 — BESS Integration**: Calculate battery capacity ($C_{bat}$) and units ($N_{bat}$) if requested.
* **US-PV05 — Financial Proposal**: Generate automated itemized BOM and preliminary financial proposal.