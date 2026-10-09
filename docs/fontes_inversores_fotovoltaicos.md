# Fontes do catálogo de inversores fotovoltaicos

Este registro acompanha `backend/data/pv/inversores.csv` e separa as fontes usadas na TASK-19:

- **fonte técnica:** ficha do fabricante usada nos campos elétricos e registrada em `url_fonte` no CSV;
- **referência comercial:** oferta brasileira usada para registrar o preço unitário em BRL.

Os preços foram coletados em **2026-10-09**, sem frete. Foi usado o preço parcelado/regular quando a oferta exibia um desconto condicionado a Pix ou boleto. Disponibilidade e preços mudam; o catálogo representa uma fotografia comercial e propostas persistidas devem manter seu próprio snapshot.

| ID | Produto | Fonte técnica | Referência comercial brasileira | Preço adotado |
|---|---|---|---|---:|
| `INV-GRO-2500-001` | Growatt MIN 2500TL-X | [Ficha Growatt MIN 2500–6000TL-X](https://au.growatt.com/upload/file/MIN_2500_6000_TL_X.pdf) | [Mercado Livre — linha MIN](https://lista.mercadolivre.com.br/inversor-growatt-min-2500tl-x) | R$ 2.899,00 |
| `INV-GRO-3000-001` | Growatt MIN 3000TL-X | [Ficha Growatt MIN 2500–6000TL-X](https://au.growatt.com/upload/file/MIN_2500_6000_TL_X.pdf) | [Minha Casa Solar](https://www.minhacasasolar.com.br/inversor-solar-monofasico-3kw-220v-2-mppt-growatt-min3000tl-x-82940) | R$ 3.224,73 |
| `INV-GRO-3600-001` | Growatt MIN 3600TL-X | [Ficha Growatt MIN 2500–6000TL-X](https://au.growatt.com/upload/file/MIN_2500_6000_TL_X.pdf) | [Mercado Livre — linha MIN](https://lista.mercadolivre.com.br/inversor-growatt-min-3600tl-x) | R$ 3.499,00 |
| `INV-GRO-4200-001` | Growatt MIN 4200TL-X | [Ficha Growatt MIN 2500–6000TL-X](https://au.growatt.com/upload/file/MIN_2500_6000_TL_X.pdf) | [Mercado Livre — linha MIN](https://lista.mercadolivre.com.br/inversor-growatt-min-4200tl-x) | R$ 3.799,00 |
| `INV-GRO-5000-001` | Growatt MIN 5000TL-X | [Ficha Growatt MIN 2500–6000TL-X](https://au.growatt.com/upload/file/MIN_2500_6000_TL_X.pdf) | [Energy Shop](https://www.energyshop.com.br/inversor-solar/inversor-grid-tie/inversor-grid-tie-growatt-5kw-monofasico-220v-2mppt) | R$ 3.999,00 |
| `INV-GRO-6000-001` | Growatt MIN 6000TL-X | [Ficha Growatt MIN 2500–6000TL-X](https://au.growatt.com/upload/file/MIN_2500_6000_TL_X.pdf) | [Minha Casa Solar](https://www.minhacasasolar.com.br/inversor-solar-monofasico-6kw-220v-2-mppt-growatt-min6000tl-x-82000) | R$ 3.699,00 |
| `INV-DEY-5000-001` | Deye SUN-5K-SG01LP1-US | [Ficha Deye SUN-(5–8)K-SG01LP1-US](https://pt.deyeinverter.com/deyeinverter/2024/11/20/datasheet_sun-5-8kk-sg01lp1-us_241120_pt.pdf) | [Apex Solar](https://www.apexenergiasolar.com.br/inversores/inversor-hibrido-deye-sun-5k-us-5000w-48120-240v-on-off-grid) | R$ 15.912,90 |
| `INV-DEY-8000-001` | Deye SUN-8K-SG01LP1-US | [Ficha Deye SUN-(5–8)K-SG01LP1-US](https://pt.deyeinverter.com/deyeinverter/2024/11/20/datasheet_sun-5-8kk-sg01lp1-us_241120_pt.pdf) | [Só Solar](https://sosolar.com.br/inversor-solar-fotovoltaico-hibrido-sun-8k-sg01lp1-us-8kw-bifasico-127-220v-2mppt-deye-p5347) | R$ 19.116,23 |

## Convenções de transcrição

- `tipo` aceita apenas `on-grid` e `hibrido`; `compativel_bateria` usa apenas `true` ou `false` em minúsculas.
- `potencia_max_fv_w` representa a potência FV máxima/recomendada informada pelo fabricante, não a potência nominal CA.
- `corrente_max_entrada_a` registra a soma das correntes operacionais máximas dos MPPTs, pois o schema da sprint possui apenas um campo agregado. A corrente não é eliminatória na Sprint 2, conforme o ADR-001.
- A faixa MPPT representa a faixa operacional geral. A TASK-25 ainda deverá considerar o arranjo de strings e não poderá interpretar a tensão de todo o conjunto como uma única string.
- Os seis modelos Growatt são inversores string sem porta de bateria. Os dois modelos Deye são híbridos de baixa tensão e garantem opções para o cenário BESS.
