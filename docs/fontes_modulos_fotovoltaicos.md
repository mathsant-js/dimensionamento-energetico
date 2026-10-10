# Fontes do catálogo de módulos fotovoltaicos

Este registro acompanha `backend/data/pv/modulos.csv` e separa as duas naturezas de fonte exigidas pela TASK-18:

- **fonte técnica:** ficha do fabricante usada nos campos elétricos em STC e registrada em `url_fonte` no CSV;
- **referência comercial:** página brasileira usada para comprovar oferta e fotografar o preço unitário em BRL.

Os preços abaixo são preços unitários anunciados, sem frete, coletados em **2026-10-09**, com a referência Leapton atualizada em **2026-10-10**. Quando uma página oferecia preço promocional condicionado a Pix/boleto, foi usado o preço regular exibido na oferta. Marketplaces e comparadores foram identificados explicitamente no campo `fornecedor`. Disponibilidade e preços podem mudar; propostas futuras devem usar uma nova fotografia do catálogo sem alterar snapshots já persistidos.

| ID | Produto | Fonte técnica | Referência comercial brasileira | Preço adotado |
|---|---|---|---|---:|
| `MOD-JAS-550-001` | JA Solar JAM72S30-550/MR | [Ficha JA Solar](https://www.jasolar.com/uploadfile/2023/0525/20230525053534178.pdf) | [Buyers Energy](https://www.buyersenergy.com.br/produtos/painel-solar-550w-ja-solar/) | R$ 634,00 |
| `MOD-CAN-550-001` | Canadian Solar CS6W-550MS | [Ficha Canadian Solar](https://solsol.eu/file/view/1186/canadian-solar-cs6w-550ms-slv-550wp_en.pdf) | [Minha Casa Solar](https://www.minhacasasolar.com.br/painel-solar-550w-monocristalino-half-cell-canadian-cs6w-550ms-82127) | R$ 589,00 |
| `MOD-JIN-555-001` | Jinko Solar JKM555N-72HL4-V | [Ficha Jinko Solar](https://www.jinkosolar.com/uploads/619f4244/JKM555-575N-72HL4-%28V%29-F1-EN.pdf) | [I9Sun Energia](https://www.i9sun.com.br/product-page/modulo-jinko-555w) | R$ 900,00 |
| `MOD-JIN-585-001` | Jinko Solar JKM585N-72HL4-V | [Ficha Jinko Solar](https://www.jinkosolar.com/uploads/JKM565-585N-72HL4-%28V%29-F4-EN.pdf) | [AchaPromo/Mercado Livre](https://achapromo.com.br/produto/painel-solar-fotovoltaica-585w-mono-jinko-energia-solar/92c7c8e3-75c8-413d-978f-14c66859273c) | R$ 1.320,00 |
| `MOD-DAH-585-001` | DAH Solar DHN-72X16/DG-585W | [Ficha DAH Solar](https://solsol.eu/file/view/1150/dah-dhn-72x16dg-580wp-slv_en.pdf) | [NeoSolar](https://www.neosolar.com.br/loja/painel-solar-fotovoltaico-585w-dah-solar-dhn-72x16.html) | R$ 779,00 |
| `MOD-DAH-620-001` | DAH Solar DHN-66Z16/DG-620W | [Ficha DAH Solar](https://cdn.enfsolar.com/z/pp/2025/5/7d9b9k7ru62i6ox3/en-dhn-66z16-dg-bw-585-625w.pdf) | [Casa do Micro Inversor](https://microinversor.com.br/produto/mod-dah620/) | R$ 821,74 |
| `MOD-GOK-620-001` | Gokin Solar GK-4-66HTBD-620M-F | [Ficha Gokin Solar](https://www.gokinsolar.com/upload/download/GK-4-66HTBD-F%20590-620%20EN-202501-IM-Fiberglass.pdf) | [NeoSolar](https://www.neosolar.com.br/loja/painel-solar-fotovoltaico-620w-gokin-gk-4-66htbd-f.html) | R$ 939,00 |
| `MOD-LEA-620-001` | Leapton Solar LP182210-M-66-NB-620W | [Ficha Leapton](https://www.leaptonenergy.jp/cms_xF2uQCfP/wp-content/uploads/2024/09/ProductSpec_LP182_210_M66_NB_620W_Ver.4.pdf) | [SGV — Mercado Livre](https://www.mercadolivre.com.br/loja/sgv?category_id=MLB270558&client=recoview-selleritems&item_id=MLB5545246184&official_store_id=103192&recos_listing=true) | R$ 819,90 |
| `MOD-RON-620-001` | Ronma Solar RM-620W-182R/132TB | [Ficha Ronma Solar](https://minhacasasolar.fbitsstatic.net/media/1.rm-600-630w-182r-132tb.pdf?v=202508140925) | [Mercado Livre](https://lista.mercadolivre.com.br/placas-solares-620w) | R$ 819,00 |
| `MOD-RES-585-001` | Resun Solar RS8I-M-DG-585W | [Ficha Resun Solar](https://www.resunsolar.com/wp-content/uploads/2025/07/RS8I-M-DG-550-585W.pdf) | [Mercado Livre](https://lista.mercadolivre.com.br/placas-solares-585w) | R$ 850,12 |

## Convenções de transcrição

- Os parâmetros elétricos são os valores frontais em condições STC (1000 W/m², 25 °C, AM 1.5), inclusive para módulos bifaciais.
- A potência indicada pelo nome do modelo identifica um produto distinto; variantes de potência da mesma família não foram usadas como registros artificiais.
- Decimais usam ponto no CSV e valores monetários representam uma unidade.
- A página comercial é evidência de mercado, não fonte de especificação quando existe ficha técnica do fabricante.
