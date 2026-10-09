# Fontes do catálogo de baterias fotovoltaicas

Este registro acompanha `backend/data/pv/baterias.csv` e separa as fontes usadas na TASK-20:

- **fonte técnica:** página ou ficha do fabricante usada nos campos de capacidade, tensão, DoD e ciclos e registrada em `url_fonte` no CSV;
- **referência comercial:** oferta acessível no mercado brasileiro usada para registrar o preço unitário em BRL.

Os preços foram coletados em **2026-10-09**, sem frete. Foi adotado o preço regular quando a página também exibia desconto condicionado a Pix. O catálogo é uma fotografia comercial: disponibilidade e preços podem mudar, e propostas persistidas devem preservar seu próprio snapshot.

| ID | Produto | Fonte técnica | Referência comercial | Preço adotado |
|---|---|---|---|---:|
| `BAT-DYN-B4850-001` | Dyness B4850 | [Ficha Dyness B4850](https://dyness.com/Public/Uploads/uploadfile/files/20241223/B4850Datasheet.pdf) | [Portal das Baterias](https://www.portaldasbaterias.com/produtos/bateria-dyness-b4850-1og8f/) | R$ 8.974,78 |
| `BAT-DYN-DL50C-001` | Dyness DL5.0C | [Ficha Dyness DL5.0C](https://dyness.com/Public/Uploads/uploadfile/files/20241128/DynessDL5.0CdatasheetBR.pdf) | [Portal das Baterias](https://www.portaldasbaterias.com/produtos/bateria-dyness-dl5-0c/) | R$ 10.780,21 |
| `BAT-DEY-SEG51-001` | Deye SE-G5.1 Pro-B | [Página técnica Deye](https://deyeess.com/product/se-g5-1-pro-b/) | [Energy Shop](https://www.energyshop.com.br/bateria-estacionaria/bateria-de-litio/bateria-litio-deye-lv-5-12kwh-se-g5-1pro-b-48v) | R$ 12.383,83 |
| `BAT-UNI-UPLFP48100-001` | Unipower UPLFP48-100 3U EN | [Ficha técnica Unipower](https://minhacasasolar.fbitsstatic.net/media/1.bateria-uplfp481003u---en.pdf?v=202510291419) | [GENAI Solar](https://genai-br.com/products/bateria-solar-litio-100ah-48v-unipower-uplfp48-100) | R$ 5.887,78 |
| `BAT-PYL-US3000C-001` | Pylontech US3000C | [Portfólio residencial Pylontech Brasil](https://pylontech.com.br/wp-content/uploads/2024/08/Pylontech-Residential-ESS-Product-Portfolio-PY240723PT-BR.pdf) | [eBay Brasil](https://br.ebay.com/b/Battery-48-V-Rechargeable-Batteries/48619/bn_7116825080) | R$ 8.259,31 |
| `BAT-PYL-US5000-001` | Pylontech US5000 | [Portfólio residencial Pylontech Brasil](https://pylontech.com.br/wp-content/uploads/2024/08/Pylontech-Residential-ESS-Product-Portfolio-PY240723PT-BR.pdf) | [Ubuy Brasil](https://www.ubuy.com.br/pt/productuk/M7HMR7UIM-pylontech-us5000-lithium-ion) | R$ 9.255,00 |

## Normalização e consistência de capacidade

- `tecnologia` usa `LiFePO4` para todos os registros; tensão está em V, capacidade elétrica em Ah, energia nominal em kWh, DoD em percentual e preço por módulo em BRL.
- A consistência é verificada por `capacidade_calculada_kwh = tensao_nominal_v × capacidade_ah / 1000`, com tolerância relativa máxima de 1% apenas para arredondamento declarado pelo fabricante.
- B4850, DL5.0C, SE-G5.1 Pro-B, UPLFP48-100 3U EN e US5000 têm igualdade exata após a normalização das unidades.
- A US3000C resulta em 3,552 kWh pelo produto de 48 V por 74 Ah; o catálogo preserva os 3,55 kWh publicados pelo fabricante. A diferença é de aproximadamente 0,056% e decorre do arredondamento para duas casas decimais.
- `capacidade_kwh` é sempre energia nominal, não energia útil. O motor de armazenamento deve aplicar o `dod_pct` uma única vez conforme o ADR-001.
- `ciclos` registra o valor mínimo nominal publicado. Condições de ensaio variam entre fabricantes (temperatura, taxa C, DoD e estado de saúde final), portanto esse campo não deve ser usado isoladamente como comparação de garantia ou vida útil real.

## Limites da referência comercial

A oferta da US5000 na Ubuy é importada e não inclui frete nem tributos de importação. Esse preço deve ser revisto antes de uma proposta comercial real. As demais referências são ofertas brasileiras dos modelos exatos catalogados; preços, estoque e condições de pagamento ainda devem ser confirmados no momento da proposta.
