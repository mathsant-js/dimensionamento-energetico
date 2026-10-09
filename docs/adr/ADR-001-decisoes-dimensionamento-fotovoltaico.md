# ADR-001 — Convenções do pré-dimensionamento fotovoltaico

- **Status:** Aceito
- **Data:** 2026-10-09
- **Task:** TASK-16
- **Escopo:** Sprint 2

## Contexto

O motor fotovoltaico depende de convenções que não estavam completamente definidas em `AGENTS.md` e que divergem parcialmente de `SPEC.md`. Sem essas decisões, implementações diferentes poderiam aplicar o DoD duas vezes, validar a tensão do arranjo pelo total de módulos, acrescentar custos implícitos ou rejeitar inversores por uma regra não aprovada.

As decisões abaixo são normativas para as TASK-17 a TASK-34. Alterações futuras exigem um novo ADR e atualização conjunta de implementação, testes e exemplos reproduzíveis.

## Decisões

### 1. Capacidade e quantidade de baterias

Será usada uma única convenção de capacidade nominal:

```text
energia_autonomia_kwh = (consumo_mensal_kwh / dias) × (autonomia_h / 24)
capacidade_nominal_requerida_kwh = energia_autonomia_kwh / (dod × eficiencia_bateria)
quantidade_baterias = ceil(capacidade_nominal_requerida_kwh / capacidade_nominal_unitaria_kwh)
capacidade_nominal_instalada_kwh = quantidade_baterias × capacidade_nominal_unitaria_kwh
energia_entregavel_instalada_kwh = capacidade_nominal_instalada_kwh × dod × eficiencia_bateria
```

`dod` e `eficiencia_bateria` são frações no intervalo `(0, 1]`. A quantidade é calculada contra a capacidade **nominal** unitária; o DoD não é aplicado novamente ao denominador. A invariante de aceite é:

```text
energia_entregavel_instalada_kwh >= energia_autonomia_kwh
```

Com autonomia igual a zero, não há armazenamento: quantidade e custos de bateria são zero e não se exige inversor híbrido.

### 2. Eficiência da bateria

A eficiência é parâmetro da simulação, pois não existe no schema obrigatório de `baterias.csv`. O valor padrão será `0,95` (95%), editável pelo usuário, validado em `(0, 1]` e persistido na proposta como snapshot. Nenhum valor será inferido do modelo da bateria.

### 3. Arranjo de strings e MPPT

O arranjo será explícito e persistido como uma lista com identificador do MPPT e quantidade de módulos da string. Nesta sprint haverá, no máximo, uma string por MPPT; strings em paralelo no mesmo MPPT ficam fora do escopo.

Para cada inversor, o seletor deve:

1. enumerar a quantidade de strings de `1` até `min(numero_modulos, numero_mppt)`;
2. distribuir os módulos da forma mais equilibrada possível: cada string recebe `floor(N/S)` módulos e as `N mod S` primeiras recebem um módulo adicional;
3. validar **cada string**, nunca o total do arranjo:
   - `voc_string = modulos_na_string × voc_modulo <= tensao_max_entrada_inversor`;
   - `vmp_string = modulos_na_string × vmp_modulo` dentro do intervalo MPPT, inclusive;
4. descartar configurações com qualquer string inválida;
5. escolher a configuração válida com menor quantidade de strings; em empate, a distribuição lexicograficamente decrescente torna o resultado determinístico.

A potência FV máxima do inversor continua sendo validada contra a potência instalada total.

### 4. Corrente de entrada

A checagem de corrente não será critério eliminatório na Sprint 2. O schema informa uma única `corrente_max_entrada_a`, mas não distingue limite por MPPT, por entrada, corrente operacional e corrente de curto-circuito; aplicar uma regra genérica poderia produzir falsos resultados.

`Isc`, `Imp` e a corrente declarada do inversor devem permanecer nos snapshots e no diagnóstico como dados informativos. A proposta deve exibir a limitação: a corrente e o detalhamento elétrico precisam ser confirmados no projeto executivo. A validação poderá ser adicionada após evolução do dataset e novo ADR.

### 5. Custos adicionais

Não será aplicado percentual implícito. Custos adicionais serão uma lista opcional e explícita de itens, cada um com `descricao` não vazia e `valor_brl >= 0`. O servidor soma os itens usando `Decimal`, com arredondamento monetário para duas casas, e persiste descrição, valor e subtotal no snapshot da proposta.

Uma lista vazia resulta em custo adicional igual a zero. O percentual de 25% de `SPEC.md` não faz parte da Sprint 2.

### 6. Carregamento FV mínimo do inversor

A regra de potência instalada mínima de 70% da potência nominal do inversor, citada em `SPEC.md`, não será usada para rejeição. Não há aprovação dessa regra em `AGENTS.md` nem critérios suficientes para torná-la universal.

Nesta sprint, a compatibilidade de potência exige apenas:

```text
potencia_instalada_w <= potencia_max_fv_w
```

### 7. Atualização de preços e rastreabilidade

`data_coleta` identifica a fotografia comercial do catálogo. Ao persistir uma proposta, preço unitário, fornecedor, URL, data de coleta e especificações relevantes são copiados para itens imutáveis da proposta.

Atualizações posteriores dos CSVs afetam apenas novas simulações e não recalculam propostas existentes. Uma edição de proposta é um recálculo integral que gera uma nova fotografia com os valores então vigentes e atualiza a data de cálculo.

## Consequências

- O cálculo de armazenamento não superdimensiona a bateria aplicando DoD duas vezes.
- As validações de Voc e Vmp passam a depender de um arranjo reproduzível.
- A Sprint 2 não promete validação elétrica executiva de corrente.
- Todo valor adicional é visível e auditável.
- Propostas históricas permanecem reproduzíveis mesmo após mudanças no catálogo.
- `SPEC.md` permanece como referência histórica; em caso de conflito nos pontos acima, este ADR prevalece para a Sprint 2.

## Casos mínimos de teste derivados

- cálculo de bateria em que a divisão pelo DoD uma única vez altera o `ceil`;
- autonomia zero sem bateria e sem restrição de inversor híbrido;
- arranjos com uma e múltiplas strings, incluindo uma string individual fora da faixa MPPT;
- limite inclusivo de Voc e dos extremos da faixa MPPT;
- custo adicional vazio e com múltiplos itens;
- inversor abaixo de 70% que continue elegível se cumprir as regras aprovadas;
- proposta cujo preço permaneça inalterado após modificação de fixture do catálogo.
