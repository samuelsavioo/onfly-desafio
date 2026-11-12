# Declaração de uso de IA

## Ferramenta e modelo

- **Ferramenta:** Claude (Anthropic), pela interface de chat claude.ai / app Claude.
- **Modelo:** Claude Sonnet 5.5.
- **Sessão exportada:** `entrega/uso-de-ia/sessao.md` (conversa completa de prompts e respostas).

## O que a IA fez

- Analisou o README e a saída do `pytest -q` e, a partir dos números de cada falha, levantou hipóteses sobre a causa de cada defeito.
- Leu os arquivos que enviei (`report_builder.py`, `currency_converter.py`, `stay_calculator.py`, `status_policy.py`, `row_parser.py` e os dois repositórios CSV) e apontou os 5 defeitos com a linha responsável:
  1. câmbio dividindo em vez de multiplicar, via `float`;
  2. noites calculadas com `.day` em vez da diferença de datas;
  3. `NO_SHOW` tratado como faturável;
  4. ranking de hotéis em ordem crescente;
  5. leitura truncada em 200 linhas (defeito não coberto pelos testes fornecidos).
- Revisou as demais regras do README (`Decimal`, `ROUND_HALF_UP`, `by_month`, média, ordem do pipeline, desempate por `hotel_id`) e indicou que já estavam corretas.
- Propôs e aplicou as correções nos cinco arquivos, e escreveu `tests/test_edge_cases.py`.
- Verificou as correções em uma cópia do projeto no ambiente da conversa, com um script de cenários e um runner mínimo no lugar do `pytest` (o ambiente não tinha `pytest` nem rede). Rodou também os testes novos contra o código original com bugs, e 7 dos 9 casos falharam, o que mostra que detectam os defeitos.
- Redigiu o rascunho do `entrega/README-ENTREGA.md` e desta declaração.

## O que eu fiz

- Li o enunciado e rodei o `pytest -q` inicial, trazendo para a conversa a saída dos 5 testes falhando e os arquivos do projeto.
- Decidi o que aplicar: antes de qualquer alteração, pedi o diagnóstico completo e as regras de negócio em risco (virada de mês/ano, filtro de status, `Decimal`, desempate do ranking) e só autorizei a correção depois.
- Copiei as correções para o meu repositório e rodei o `pytest -q` de verdade: os 5 testes fornecidos passaram.
- Rodei o CLI na amostra `exemplo-validacao.csv` e comparei com a tabela do README (12 reservas, 9 confirmadas, 28 noites, `7566.00`), que bateu.
- Rodei o CLI no `reservas_hoteis.csv` completo e confirmei que as 300 reservas foram lidas, sem corte em 200 (235 confirmadas, 1347 noites, `396170.00`).
- Adicionei `tests/test_edge_cases.py` ao repositório e rodei o `pytest -q`: **14 passed**.
- Revisei e ajustei os textos de entrega antes de publicar.
