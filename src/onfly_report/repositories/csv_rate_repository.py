"""Leitura da tabela de taxas de câmbio em CSV."""

from __future__ import annotations

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..exceptions import InputFileError

REQUIRED_COLUMNS = ("currency", "rate_to_brl")


class CsvRateRepository:
    """Lê as taxas de câmbio e devolve um mapa moeda -> Decimal."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> dict[str, Decimal]:
        try:
            with self._path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
                if missing:
                    raise InputFileError(f"colunas obrigatórias ausentes: {', '.join(missing)}")

                rates: dict[str, Decimal] = {}
                for row in reader:
                    currency = (row.get("currency") or "").strip()
                    raw_rate = (row.get("rate_to_brl") or "").strip()
                    if not currency or not raw_rate:
                        raise InputFileError(f"linha {reader.line_num}: taxa de câmbio inválida")
                    try:
                        rates[currency] = Decimal(raw_rate)
                    except InvalidOperation as err:
                        raise InputFileError(
                            f"linha {reader.line_num}: taxa inválida '{raw_rate}'"
                        ) from err
                return rates
        except FileNotFoundError as err:
            raise InputFileError(f"arquivo de taxas não encontrado: {self._path}") from err
        except (OSError, csv.Error) as err:
            raise InputFileError(f"falha ao ler {self._path}: {err}") from err