# Guia Visual - Relatório de Consumo de Energia

## Componentes da Interface

### 1. Card "Maior Consumidor" (Topo do Relatório)

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚡ Maior Consumidor                                              │
│                                                                 │
│    Ar Condicionado 12000 BTU                                    │
│    360.00 kWh/mês (50.0% do total)                             │
└─────────────────────────────────────────────────────────────────┘
```

**Características:**
- Fundo vermelho-claro (#fee2e2) com borda vermelha
- Ícone ⚡ para destaque imediato
- Nome do equipamento em destaque (fonte grande)
- Consumo em kWh/mês
- Percentual do consumo total

---

### 2. Tabela de Comparação (Equipamentos Ordenados)

```
┌──────────────────┬──────────────┬──────────┬──────────┬─────────┬────────────────┐
│ Equipamento      │ Potência (W) │ Qtd      │ Horas/d  │ kWh/mês │ % do Total     │
├──────────────────┼──────────────┼──────────┼──────────┼─────────┼────────────────┤
│ ⚡ Ar Condic.   │ 1500         │ 1        │ 8.0      │ 360.00  │ ███████████░░░ │
│                  │              │          │          │         │         50.0%  │
├──────────────────┼──────────────┼──────────┼──────────┼─────────┼────────────────┤
│ Chuveiro Elét.   │ 5500         │ 1        │ 1.0      │ 165.00  │ ████████░░░░░░ │
│                  │              │          │          │         │         23.0%  │
├──────────────────┼──────────────┼──────────┼──────────┼─────────┼────────────────┤
│ Geladeira        │ 500          │ 1        │ 24.0     │ 360.00  │ ██████░░░░░░░░ │
│                  │              │          │          │         │         18.0%  │
└──────────────────┴──────────────┴──────────┴──────────┴─────────┴────────────────┘
```

**Características:**
- Equipamentos ordenados DO MAIOR para o MENOR consumo
- Linha do maior consumidor destacada (fundo #fef2f2)
- Badge ⚡ na coluna do equipamento com maior consumo
- Barras de percentual visuais (coluna "% do Total")
- Cor vermelha para o maior consumidor
- Cor azul para demais equipamentos
- Percentual sempre visível ao lado da barra

---

### 3. Resumo (Rodapé do Relatório)

```
┌───────────────────────────────────────────────────────────────┐
│                                                               │
│  Total de Equipamentos: 9    Maior Consumidor: Ar Cond.      │
│                                                               │
│              Consumo Total Mensal: 720.25 kWh                │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Características:**
- 3 cards com informações principais
- Card total destacado em azul gradiente
- Fonte grande para impacto visual
- Fácil leitura e compreensão

---

## Fluxo de Comparação

### Algoritmo de Identificação do Maior Consumidor

```javascript
// 1. Encontrar o maior consumidor
const highestConsumer = items.reduce((max, item) => 
  item.consumption > max.consumption ? item : max
);

// 2. Ordenar todos pelo consumo (maior primeiro)
const sorted = items.sort((a, b) => b.consumption - a.consumption);

// 3. Calcular percentual de cada um
const withPercentage = sorted.map(item => ({
  ...item,
  percentage: (item.consumption / total) * 100
}));
```

### Indicadores Visuais

| Elemento | Função | Cor | Posição |
|----------|--------|-----|---------|
| Card "Maior Consumidor" | Alerta visual do equipamento mais consumidor | Vermelho (#dc2626) | Topo |
| Badge ⚡ | Identificar rapidamente na tabela | Vermelho | Coluna Equipamento |
| Linha Destacada | Destacar linha do maior consumidor | Vermelho-claro (#fef2f2) | Tabela |
| Barra Vermelha | Visualizar proporção do maior consumidor | Vermelho | Coluna % |
| Barra Azul | Visualizar proporção dos demais | Azul (#3b82f6) | Coluna % |
| Texto Percentual | Valor exato do percentual | Cinza escuro | Coluna % |

---

## Exemplos de Cenários

### Cenário 1: Chuveiro é o Vilão

```
├─ Chuveiro Elétrico ............... 1650 kWh/mês (65%)   [████████████████░░]
├─ Ar Condicionado ................ 360 kWh/mês  (14%)   [███░░░░░░░░░░░░░░]
├─ Geladeira ..................... 360 kWh/mês  (14%)   [███░░░░░░░░░░░░░░]
└─ Demais ......................... 180 kWh/mês  (7%)    [██░░░░░░░░░░░░░░░]
```

**Maior Consumidor:** Chuveiro Elétrico (65% - 1650 kWh/mês)

---

### Cenário 2: Ar Condicionado é o Vilão

```
├─ Ar Condicionado 18000 BTU ....... 1440 kWh/mês (45%)  [█████████░░░░░░░░]
├─ Chuveiro Elétrico .............. 165 kWh/mês  (5%)   [░░░░░░░░░░░░░░░░░]
├─ Aquecedor de Água ............. 900 kWh/mês  (28%)  [██████░░░░░░░░░░░]
├─ Máquina de Lavar ............... 400 kWh/mês  (13%)  [███░░░░░░░░░░░░░░]
└─ Demais ......................... 195 kWh/mês  (6%)   [█░░░░░░░░░░░░░░░░]
```

**Maior Consumidor:** Ar Condicionado 18000 BTU (45% - 1440 kWh/mês)

---

### Cenário 3: Consumo Bem Distribuído

```
├─ Ar Condicionado ................ 360 kWh/mês  (23%)  [████░░░░░░░░░░░░]
├─ Chuveiro Elétrico .............. 330 kWh/mês  (21%)  [███░░░░░░░░░░░░░]
├─ Geladeira ..................... 360 kWh/mês  (23%)  [████░░░░░░░░░░░░]
├─ Aquecedor de Água ............. 300 kWh/mês  (19%)  [███░░░░░░░░░░░░░]
└─ Demais ......................... 210 kWh/mês  (13%)  [██░░░░░░░░░░░░░░]
```

**Maior Consumidor:** Ar Condicionado (23% - 360 kWh/mês)

---

## Responsividade Mobile

### Desktop (> 768px)
- Tabela completa com 6 colunas
- Card de alerta em linha com layout horizontal
- Resumo em 3 cards lado a lado

### Tablet (768px)
- Tabela com colunas menores
- Card de alerta ainda em linha
- Resumo em 1 coluna (stack vertical)

### Mobile (< 768px)
- Tabela com fonte reduzida (12px)
- Card de alerta em coluna (ícone acima, texto abaixo)
- Resumo totalmente stacked
- Barras de percentual ocupam 100% da largura
- Fonte otimizada para leitura em tela pequena

---

## Integração com Backend

### Dados Retornados pela API

```json
{
  "property_id": 1,
  "property_name": "Casa Principal",
  "property_type": "casa",
  "items": [
    {
      "id": 1,
      "equipment_name": "Ar Condicionado 12000 BTU",
      "power_watts": 1500,
      "quantity": 1,
      "hours_per_day": 8,
      "monthly_consumption_kwh": 360
    },
    {
      "id": 2,
      "equipment_name": "Geladeira",
      "power_watts": 500,
      "quantity": 1,
      "hours_per_day": 24,
      "monthly_consumption_kwh": 360
    }
  ],
  "total_monthly_consumption_kwh": 720,
  "created_at": "2026-10-05T01:56:38.650-03:00"
}
```

### Processamento no Frontend

```typescript
// 1. Recebe o relatório da API
const report = response.data;

// 2. Identifica o maior consumidor
const highest = report.items.reduce((max, item) =>
  item.monthly_consumption_kwh > max.monthly_consumption_kwh ? item : max
);

// 3. Ordena e calcula percentuais
const sorted = report.items.sort((a, b) => 
  b.monthly_consumption_kwh - a.monthly_consumption_kwh
).map(item => ({
  ...item,
  percentage: (item.monthly_consumption_kwh / report.total_monthly_consumption_kwh) * 100
}));

// 4. Renderiza com indicadores visuais
// - Card com dados do maior consumidor
// - Tabela com linhas ordenadas
// - Badge e destaque visual para o maior
// - Barras de percentual dinâmicas
```

---

## Próximos Passos de Visualização

1. **Gráfico de Pizza**: Mostrar proporção visual de cada equipamento
2. **Gráfico de Barras**: Comparação lado a lado dos consumos
3. **Timeline**: Evolução do consumo ao longo dos meses
4. **Badges de Eficiência**: Categorizar equipamentos como "Alto consumo", "Normal", "Eficiente"
5. **Dicas Interativas**: Sugestões de redução de consumo ao hover sobre equipamentos

---

**Desenvolvido para facilitar a compreensão do consumo energético através de visualizações claras e intuitivas.**
