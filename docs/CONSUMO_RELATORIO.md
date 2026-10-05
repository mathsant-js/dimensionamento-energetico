# Relatório de Consumo de Energia - Documentação

## Visão Geral

O novo recurso de **Relatório de Consumo** permite que os usuários visualizem um resumo detalhado do consumo energético de suas propriedades. O relatório apresenta uma tabela com todos os equipamentos cadastrados e seus respectivos consumos mensais em kWh, além de um total agregado.

## Critérios de Aceite Implementados

✅ **Exibir o nome do imóvel e a tabela com os equipamentos, potências, quantidades e horas/dia.**
- A tela de relatório mostra o nome da propriedade no cabeçalho
- Uma tabela apresenta:
  - **Equipamento**: Nome do equipamento (ex: "Geladeira", "Ar Condicionado")
  - **Potência (W)**: Potência nominal em watts
  - **Quantidade**: Quantidade de unidades daquele equipamento
  - **Horas/dia**: Horas de uso médio por dia (0-24)

✅ **Exibir os valores calculados individualmente e a soma total final em kWh / mês.**
- **Consumo Mensal (kWh)** por equipamento é calculado usando a fórmula:
  ```
  Consumo Mensal = (Potência em W × Quantidade × Horas por dia × 30 dias) / 1000
  ```
- **Total de Consumo Mensal** é apresentado em destaque no final do relatório

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
