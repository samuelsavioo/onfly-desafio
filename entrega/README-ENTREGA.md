# Entrega: Consolidador de reservas de hotel (Onfly)

O CLI gerava números errados por cinco defeitos independentes na camada de serviços e na leitura do CSV. Todos foram corrigidos sem alterar o contrato do CLI, o schema do relatório, os testes fornecidos nem os arquivos de `data/`.

## Defeitos corrigidos

| # | Arquivo | Defeito | Causa raiz (uma frase) |
|---|---------|---------|------------------------|
| 1 | `src/onfly_report/services/currency_converter.py` | Valores em moeda estrangeira convertidos de forma errada | A conversão **dividia** pela taxa em vez de multiplicar e passava por `float`, perdendo exatidão. |
| 2 | `src/onfly_report/services/stay_calculator.py` | Noites negativas ou erradas na virada de mês/ano | O cálculo subtraía só o dia do mês (`checkout.day - checkin.day`) em vez da diferença real entre as datas. |
| 3 | `src/onfly_report/services/status_policy.py` | `NO_SHOW` entrava em noites, valores, `by_month` e `top_hotels` | `is_billable` só excluía `CANCELLED` (`status != "CANCELLED"`), quando só `CONFIRMED` é faturável. |
| 4 | `src/onfly_report/services/report_builder.py` | `top_hotels` mostrava os hotéis de menor valor | A ordenação usava `amount` crescente, e o `--top` cortava os menores. |
| 5 | `src/onfly_report/repositories/csv_reservation_repository.py` | Reservas além da 200ª eram ignoradas | Um `if len(rows) == 200: break` truncava a leitura do arquivo. |

### Correções aplicadas

```python
# 1. currency_converter.py
return amount * rates[currency]

# 2. stay_calculator.py
return (checkout - checkin).days * rooms

# 3. status_policy.py
return status == "CONFIRMED"

# 4. report_builder.py (nega só o valor, para o desempate por hotel_id continuar ascendente)
ranked_hotels = sorted(hotels.items(), key=lambda item: (-item[1]["amount"], item[0]))

# 5. csv_reservation_repository.py
# removido: if len(rows) == 200: break
```

## Como investiguei

1. **Partindo das falhas do `pytest -q`.** Os 5 testes falhavam, e os números do erro já indicavam a causa:
   - câmbio: `118.45` em vez de `642.00` é `100 + 100/5.42`, ou seja, divisão no lugar de multiplicação;
   - noites: `-28` para 30/01 → 02/02 é `2 - 30`, ou seja, só o dia do mês;
   - status: `120.00` em vez de `100.00` é `100 + 20`, ou seja, o `NO_SHOW` entrando no total;
   - ranking: `H04, H03, H02` é a ordem crescente;
   - o teste de regressão (`1018.45` em vez de `1542.00`) é `1000 + 18.45`, o mesmo defeito do câmbio.
2. **Lendo o código para confirmar cada hipótese.** Os defeitos 1 a 4 ficavam exatamente onde os números apontavam.
3. **Revisando as demais regras de negócio do README.** Conferi que já estavam corretas: uso de `Decimal` na leitura e na soma, arredondamento só na serialização com `ROUND_HALF_UP`, média `"0.00"` sem noites, `by_month` pelo mês do check-in com ordenação ascendente, e a ordem do pipeline (contar status antes de filtrar `CONFIRMED`).
4. **Encontrando o defeito 5 pela leitura do repositório.** Ele não aparece nos testes fornecidos, porque os dados deles são pequenos. Só se manifesta em arquivos com mais de 200 reservas, como o `data/reservas_hoteis.csv` completo.
5. **Atenção ao desempate do ranking.** Usar `reverse=True` no defeito 4 inverteria também o `hotel_id`, violando a regra. Por isso a correção nega apenas o valor.

## Testes adicionados

`tests/test_edge_cases.py` (autocontido; não altera os testes fornecidos) cobre o que os testes originais não cobriam:

- arquivo com 200, 201 e 350 reservas (sem truncamento);
- empate no ranking com desempate por `hotel_id` ascendente, inclusive com `--top` e com empate após conversão de câmbio (100 USD = 542 BRL);
- virada de ano (30/12/2025 → 02/01/2026, 2 quartos = 6 noites) e dia bissexto (28/02 → 01/03/2024);
- nenhuma reserva `CONFIRMED`: valores e média em `"0.00"`, `by_month` e `top_hotels` vazios, contagens por status preservadas.

## Como validar

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

# testes
pytest -q

# amostra de validação do README
PYTHONPATH=src python -m onfly_report \
  --input data/exemplo-validacao.csv \
  --rates data/taxas_cambio.csv \
  --output output/exemplo.json

# dataset completo
PYTHONPATH=src python -m onfly_report \
  --input data/reservas_hoteis.csv \
  --rates data/taxas_cambio.csv \
  --output output/report.json
```

## Resultado

**`pytest -q`:**

```
14 passed
```

São 5 testes fornecidos (inalterados) e 9 casos novos de `tests/test_edge_cases.py`.

**Amostra `exemplo-validacao.csv`:** bate com a tabela do README: 12 reservas (9 confirmadas), 28 noites de quarto e total de `7566.00`.

**Dataset completo `reservas_hoteis.csv`:** lê as 300 reservas, sem truncar em 200:

| Campo | Valor |
|-------|-------|
| `total_reservations` | 300 |
| `confirmed_reservations` | 235 |
| `total_room_nights` | 1347 |
| `total_amount_brl` | 396170.00 |

## Observação

Mantive o código fora desses cinco pontos como estava. Não alterei, por exemplo, a normalização de caixa de `status` e `currency` no `row_parser.py`, porque o README garante que os dados são consistentes.
