# Relatório de Consumo de Energia - Documentação

## Visão Geral

O novo recurso de **Relatório de Consumo** permite que os usuários visualizem um resumo detalhado do consumo energético de suas propriedades. O relatório apresenta:

1. **Alerta do Maior Consumidor**: Card destacado indicando qual equipamento consome mais energia
2. **Tabela de Comparação**: Equipamentos ordenados por consumo com barras de percentual visuais
3. **Resumo Agregado**: Total de consumo mensal e estatísticas

## Critérios de Aceite Implementados

✅ **Exibir o nome do imóvel e a tabela com os equipamentos, potências, quantidades e horas/dia.**
- A tela de relatório mostra o nome da propriedade no cabeçalho
- Uma tabela apresenta:
  - **Equipamento**: Nome do equipamento com badge para maior consumidor
  - **Potência (W)**: Potência nominal em watts
  - **Quantidade**: Quantidade de unidades daquele equipamento
  - **Horas/dia**: Horas de uso médio por dia (0-24)

✅ **Exibir os valores calculados individualmente e a soma total final em kWh / mês.**
- **Consumo Mensal (kWh)** por equipamento é calculado usando a fórmula:
  ```
  Consumo Mensal = (Potência em W × Quantidade × Horas por dia × 30 dias) / 1000
  ```
- **Total de Consumo Mensal** é apresentado em destaque no final do relatório

✅ **Comparar os consumos calculados em kWh / mês de todos os equipamentos do imóvel.**
- Equipamentos são automaticamente **ordenados do maior para o menor consumo**
- Coluna **"% do Total"** mostra graficamente a proporção de cada equipamento com barra visual

✅ **Indicar visualmente e por texto qual equipamento possui o maior consumo estimado.**
- **Card de Alerta "Maior Consumidor"** no topo com:
  - Ícone ⚡ de destaque
  - Nome do equipamento
  - Consumo em kWh/mês
  - Percentual do consumo total
- **Linha destacada na tabela** com fundo vermelho-claro
- **Badge ⚡** na coluna do equipamento com maior consumo

## Arquitetura da Solução

### Backend (Python/FastAPI)

#### Modelos (`app/models/equipment.py`)
```python
class Equipment
- id: Identificador único
- name: Nome do equipamento
- category: Categoria (ex: Refrigeração, Climatização)
- power_watts: Potência em watts
- created_at: Data de criação

class PropertyEquipment
- id: Identificador único
- property_id: Referência à propriedade
- equipment_id: Referência ao equipamento
- quantity: Quantidade de unidades
- hours_per_day: Horas de uso por dia
- created_at: Data de criação
```

#### Schemas (`app/schemas/equipment.py`)
- `EquipmentRead`: Dados de um equipamento
- `PropertyEquipmentRead`: Equipamento associado a uma propriedade
- `ConsumptionReportItem`: Item individual no relatório
- `ConsumptionReport`: Relatório completo com todos os itens

#### CRUD (`app/crud/equipment.py`)
- `get_all_equipments()`: Lista todos os equipamentos
- `create_equipment()`: Cria um novo equipamento
- `get_property_equipments()`: Lista equipamentos de uma propriedade
- `create_property_equipment()`: Associa equipamento a uma propriedade
- `update_property_equipment()`: Atualiza uso do equipamento
- `delete_property_equipment()`: Remove equipamento de uma propriedade
- `get_consumption_report()`: Gera o relatório de consumo (sem modificação - lógica no frontend)

#### Endpoints API

**Equipamentos:**
- `GET /equipments/` - Lista todos os equipamentos disponíveis
- `POST /equipments/` - Cria um novo equipamento

**Equipamentos da Propriedade:**
- `GET /properties/{property_id}/equipments/` - Lista equipamentos da propriedade
- `POST /properties/{property_id}/equipments/` - Adiciona equipamento à propriedade
- `PUT /properties/{property_id}/equipments/{equipment_id}` - Atualiza uso do equipamento
- `DELETE /properties/{property_id}/equipments/{equipment_id}` - Remove equipamento

**Relatório:**
- `GET /properties/{property_id}/consumption-report` - Retorna o relatório de consumo

### Frontend (React/TypeScript)

#### Componentes

**`ConsumptionReport.tsx`** (`frontend/src/components/properties/`)
- Componente principal do relatório com recursos avançados:
  - **Identificação de maior consumidor**: Usa `reduce()` para encontrar o equipamento com maior consumo
  - **Ordenação**: Equipamentos ordenados por consumo (maior primeiro)
  - **Cálculo de percentual**: Cada item recebe `percentage = (consumption / total) * 100`
  - **Indicadores visuais**: Badge ⚡, linha destacada, card de alerta
  - **Barras de percentual**: Visualização gráfica da proporção de consumo
  - Estados: loading, error, report data
  - Interface responsiva para mobile

**Lógica de Comparação:**
```typescript
// Encontra o maior consumidor
const highestConsumer = report.items.reduce((max, item) => 
  item.monthly_consumption_kwh > max.monthly_consumption_kwh ? item : max
);

// Ordena por consumo decrescente
const sortedItems = [...report.items].sort((a, b) => 
  b.monthly_consumption_kwh - a.monthly_consumption_kwh
);

// Calcula percentual de cada item
const itemsWithPercentage = sortedItems.map(item => ({
  ...item,
  percentage: (item.monthly_consumption_kwh / report.total_monthly_consumption_kwh) * 100
}));
```

**Tipos** (`frontend/src/types/equipment.ts`)
```typescript
interface Equipment
interface PropertyEquipment
interface ConsumptionReport
interface ConsumptionReportItem
```

#### Estilização (`ConsumptionReport.css`)
- **Card "Maior Consumidor"**: Fundo vermelho-claro com ícone ⚡
- **Tabela com destaque**: Linha do maior consumidor em destaque
- **Barras de percentual**: Animação visual com cores dinâmicas
- **Layout responsivo**: Suporte total para mobile
- **Indicadores visuais**: Cores, badges e ícones para melhor compreensão

### Dados Seed (`backend/app/seed.py`)

Lista de 20 equipamentos pré-cadastrados:
- Refrigeração: Geladeira, Freezer
- Climatização: Ar Condicionado (12000, 18000 BTU), Ventilador
- Aquecimento: Chuveiro, Aquecedor
- Limpeza: Ferro, Máquina de Lavar, Secadora
- Cozinha: Micro-ondas, Forno, Fogão, Liquidificador
- Entretenimento: Televisão
- Eletrônicos: Computador, Notebook, Impressora
- Iluminação: Lâmpadas LED, Fluorescentes

## Como Usar

### 1. Acessar o Relatório
1. Faça login no aplicativo
2. Na lista de propriedades, clique no botão **"Relatório"** de uma propriedade
3. O relatório de consumo será carregado com comparações

### 2. Interpretar os Dados

#### Card "Maior Consumidor"
Mostra qual equipamento consome mais energia:
- **Ícone ⚡**: Destaca equipamento de alto consumo
- **Nome do equipamento**: Identificação clara
- **Consumo (kWh/mês)**: Valor absoluto
- **Percentual**: Qual % do consumo total representa

#### Tabela de Comparação
- **Ordem**: Do maior para o menor consumo
- **Badge ⚡**: Marca o equipamento de maior consumo
- **% do Total**: Barra visual com percentual
  - Vermelho: Maior consumidor
  - Azul: Demais equipamentos
  - Valores sempre visíveis

#### Resumo
- **Total de Equipamentos**: Quantidade cadastrada
- **Equipamento com Maior Consumo**: Nome do campeão de consumo
- **Consumo Total Mensal**: Soma de todo o consumo

### 3. Adicionar Equipamentos (Futuro)
Atualmente, o endpoint existe mas a UI para adicionar equipamentos será desenvolvida na próxima fase. Você pode usar a API diretamente:

```bash
# Adicionar um equipamento a uma propriedade
curl -X POST http://localhost:8000/properties/1/equipments/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": 1,
    "quantity": 2,
    "hours_per_day": 8
  }'
```

## Fórmulas Utilizadas

### Consumo Mensal por Equipamento
```
Consumo (kWh) = (Potência em W × Quantidade × Horas/dia × 30) / 1000
```

**Exemplo:**
- Geladeira: 500W × 1 × 24h × 30 = 360 kWh/mês
- Ar Condicionado: 1500W × 1 × 8h × 30 = 360 kWh/mês
- Televisão: 150W × 1 × 6h × 30 = 27 kWh/mês

### Percentual do Total
```
Percentual = (Consumo do Equipamento / Consumo Total) × 100%
```

### Identificação de Maior Consumidor
```
MaiorConsumidor = MAX(todos os consumos)
```

## Segurança

- ✅ Autenticação JWT obrigatória
- ✅ Isolamento de dados por usuário
- ✅ Verificação de propriedade (usuário só vê suas propriedades)
- ✅ Validação de entrada em todos os endpoints

## Próximas Melhorias

1. **UI para Adicionar/Editar Equipamentos**
   - Formulário para associar equipamentos a propriedades
   - Gerenciamento de quantidade e horas/dia

2. **Gráficos Avançados**
   - Pizza chart mostrando proporção de consumo
   - Gráfico de barras com equipamentos mais consumidores
   - Timeline de consumo por mês (histórico)

3. **Exportação de Relatório**
   - Download em PDF com todas as análises
   - Exportação para Excel com dados brutos
   - Envio por email

4. **Recomendações de Eficiência**
   - Identificar equipamentos antiquados
   - Sugestões de redução de consumo
   - Estimativa de economia com mudanças

5. **Integração com Dimensionamento PV**
   - Usar o consumo total como base para cálculos solares
   - Sugerir tamanho de sistema fotovoltaico necessário
   - Gerar propostas de sistemas com ROI estimado

## Teste com Dados de Exemplo

Para popular o banco com dados de teste:

```bash
cd backend
python3 seed_test_data.py
```

Isso adicionará equipamentos de exemplo a uma propriedade de teste com consumos realistas, demonstrando a funcionalidade de comparação e indicação do maior consumidor.

## Estrutura de Arquivos

```
backend/
├── app/
│   ├── models/
│   │   └── equipment.py          # Modelos de equipamento
│   ├── schemas/
│   │   └── equipment.py          # Schemas de validação
│   ├── crud/
│   │   └── equipment.py          # Operações de banco
│   ├── seed.py                   # Seed de equipamentos
│   └── main.py                   # Endpoints da API
└── seed_test_data.py             # Script de dados de teste

frontend/
└── src/
    ├── components/
    │   └── properties/
    │       ├── ConsumptionReport.tsx      # Componente do relatório com comparação
    │       ├── ConsumptionReport.css      # Estilos da comparação
    │       └── PropertyList.tsx           # Lista com botão "Relatório"
    └── types/
        └── equipment.ts                   # Tipos TypeScript
```

---

**Desenvolvido com ❤️ para sustentabilidade energética**
**Versão 2.0 - Com Comparação e Indicador de Maior Consumidor**

## Arquitetura da Solução

### Backend (Python/FastAPI)

#### Modelos (`app/models/equipment.py`)
```python
class Equipment
- id: Identificador único
- name: Nome do equipamento
- category: Categoria (ex: Refrigeração, Climatização)
- power_watts: Potência em watts
- created_at: Data de criação

class PropertyEquipment
- id: Identificador único
- property_id: Referência à propriedade
- equipment_id: Referência ao equipamento
- quantity: Quantidade de unidades
- hours_per_day: Horas de uso por dia
- created_at: Data de criação
```

#### Schemas (`app/schemas/equipment.py`)
- `EquipmentRead`: Dados de um equipamento
- `PropertyEquipmentRead`: Equipamento associado a uma propriedade
- `ConsumptionReportItem`: Item individual no relatório
- `ConsumptionReport`: Relatório completo com todos os itens

#### CRUD (`app/crud/equipment.py`)
- `get_all_equipments()`: Lista todos os equipamentos
- `create_equipment()`: Cria um novo equipamento
- `get_property_equipments()`: Lista equipamentos de uma propriedade
- `create_property_equipment()`: Associa equipamento a uma propriedade
- `update_property_equipment()`: Atualiza uso do equipamento
- `delete_property_equipment()`: Remove equipamento de uma propriedade
- `get_consumption_report()`: Gera o relatório de consumo

#### Endpoints API

**Equipamentos:**
- `GET /equipments/` - Lista todos os equipamentos disponíveis
- `POST /equipments/` - Cria um novo equipamento

**Equipamentos da Propriedade:**
- `GET /properties/{property_id}/equipments/` - Lista equipamentos da propriedade
- `POST /properties/{property_id}/equipments/` - Adiciona equipamento à propriedade
- `PUT /properties/{property_id}/equipments/{equipment_id}` - Atualiza uso do equipamento
- `DELETE /properties/{property_id}/equipments/{equipment_id}` - Remove equipamento

**Relatório:**
- `GET /properties/{property_id}/consumption-report` - Retorna o relatório de consumo

### Frontend (React/TypeScript)

#### Componentes

**`ConsumptionReport.tsx`** (`frontend/src/components/properties/`)
- Componente principal do relatório
- Estados: loading, error, report data
- Exibe tabela de equipamentos com cálculos
- Mostra resumo com total de consumo
- Interface responsiva

**Tipos** (`frontend/src/types/equipment.ts`)
```typescript
interface Equipment
interface PropertyEquipment
interface ConsumptionReport
interface ConsumptionReportItem
```

#### Estilização (`ConsumptionReport.css`)
- Layout responsivo
- Tabela formatada com cores
- Cards de resumo destacados
- Suporte mobile

### Dados Seed (`backend/app/seed.py`)

Lista de 20 equipamentos pré-cadastrados:
- Refrigeração: Geladeira, Freezer
- Climatização: Ar Condicionado (12000, 18000 BTU), Ventilador
- Aquecimento: Chuveiro, Aquecedor
- Limpeza: Ferro, Máquina de Lavar, Secadora
- Cozinha: Micro-ondas, Forno, Fogão, Liquidificador
- Entretenimento: Televisão
- Eletrônicos: Computador, Notebook, Impressora
- Iluminação: Lâmpadas LED, Fluorescentes

## Como Usar

### 1. Acessar o Relatório
1. Faça login no aplicativo
2. Na lista de propriedades, clique no botão **"Relatório"** de uma propriedade
3. O relatório de consumo será carregado

### 2. Interpretar os Dados
- **Tabela de Equipamentos**: Mostra todos os aparelhos e seu consumo individual
- **Total Mensal**: Soma todos os consumos em kWh por mês
- **Consumo em kWh**: Valores são calculados automaticamente baseado na fórmula

### 3. Adicionar Equipamentos (Futuro)
Atualmente, o endpoint existe mas a UI para adicionar equipamentos será desenvolvida na próxima fase. Você pode usar a API diretamente:

```bash
# Adicionar um equipamento a uma propriedade
curl -X POST http://localhost:8000/properties/1/equipments/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "equipment_id": 1,
    "quantity": 2,
    "hours_per_day": 8
  }'
```

## Fórmulas Utilizadas

### Consumo Mensal por Equipamento
```
Consumo (kWh) = (Potência em W × Quantidade × Horas/dia × 30) / 1000
```

**Exemplo:**
- Geladeira: 500W × 1 × 24h × 30 = 360 kWh/mês
- Ar Condicionado: 1500W × 1 × 8h × 30 = 360 kWh/mês
- Televisão: 150W × 1 × 6h × 30 = 27 kWh/mês

### Consumo Total Mensal
```
Total = Σ (Consumo de cada equipamento)
```

## Segurança

- ✅ Autenticação JWT obrigatória
- ✅ Isolamento de dados por usuário
- ✅ Verificação de propriedade (usuário só vê suas propriedades)
- ✅ Validação de entrada em todos os endpoints

## Próximas Melhorias

1. **UI para Adicionar/Editar Equipamentos**
   - Formulário para associar equipamentos a propriedades
   - Gerenciamento de quantidade e horas/dia

2. **Gráficos de Consumo**
   - Visualização em gráficos de pizza e barras
   - Comparação histórica

3. **Exportação de Relatório**
   - Download em PDF
   - Exportação para Excel

4. **Análise e Recomendações**
   - Identificar equipamentos de alto consumo
   - Sugestões de eficiência energética

5. **Integração com Dimensionamento PV**
   - Usar o consumo total como base para cálculos solares
   - Gerar propostas de sistemas fotovoltaicos

## Teste com Dados de Exemplo

Para popular o banco com dados de teste:

```bash
cd backend
python3 seed_test_data.py
```

Isso adicionará equipamentos de exemplo a uma propriedade de teste com consumos realistas.

## Estrutura de Arquivos

```
backend/
├── app/
│   ├── models/
│   │   └── equipment.py          # Novos modelos
│   ├── schemas/
│   │   └── equipment.py          # Novos schemas
│   ├── crud/
│   │   └── equipment.py          # Novos CRUD operations
│   ├── seed.py                   # Seed de equipamentos
│   └── main.py                   # Endpoints adicionados
└── seed_test_data.py             # Script de teste

frontend/
└── src/
    ├── components/
    │   └── properties/
    │       ├── ConsumptionReport.tsx      # Componente novo
    │       ├── ConsumptionReport.css      # Estilos novo
    │       └── PropertyList.tsx           # Atualizado
    └── types/
        └── equipment.ts                   # Tipos novos
```

---

**Desenvolvido com ❤️ para sustentabilidade energética**
