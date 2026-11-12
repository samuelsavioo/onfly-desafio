"""Casos de borda adicionais, sem depender dos helpers dos testes fornecidos."""

from __future__ import annotations

import csv
import json

import pytest

from onfly_report.cli import main

COLUMNS = [
    "reservation_id", "traveler_name", "company_id", "hotel_id", "hotel_name", "city",
    "country", "checkin_date", "checkout_date", "rooms", "status", "currency", "amount",
    "payment_method", "booked_at",
]

DEFAULTS = {
    "traveler_name": "Viajante",
    "company_id": "C01",
    "hotel_id": "H01",
    "hotel_name": "Hotel A",
    "city": "São Paulo",
    "country": "BR",
    "checkin_date": "2025-01-10",
    "checkout_date": "2025-01-11",
    "rooms": "1",
    "status": "CONFIRMED",
    "currency": "BRL",
    "amount": "100.00",
    "payment_method": "CARD",
    "booked_at": "2025-01-01",
}

RATES = "currency,rate_to_brl\nBRL,1.00\nUSD,5.42\n"


def run_report(tmp_path, rows, top=5):
    """Grava os CSVs, executa o CLI e devolve o relatório JSON."""
    input_path = tmp_path / "reservas.csv"
    rates_path = tmp_path / "taxas.csv"
    output_path = tmp_path / "report.json"

    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for index, row in enumerate(rows, start=1):
            writer.writerow({**DEFAULTS, "reservation_id": f"R-{index}", **row})
    rates_path.write_text(RATES, encoding="utf-8")

    exit_code = main(
        [
            "--input", str(input_path),
            "--rates", str(rates_path),
            "--output", str(output_path),
            "--top", str(top),
        ]
    )
    assert exit_code == 0
    return json.loads(output_path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("total", [200, 201, 350])
def test_file_with_more_than_200_rows_is_fully_read(tmp_path, total):
    """O arquivo inteiro é processado, sem truncar em 200 linhas."""
    report = run_report(tmp_path, [{"amount": "10.00"} for _ in range(total)])

    summary = report["summary"]
    assert summary["total_reservations"] == total
    assert summary["confirmed_reservations"] == total
    assert summary["total_room_nights"] == total
    assert summary["total_amount_brl"] == f"{total * 10}.00"


def test_ranking_tie_is_broken_by_hotel_id_ascending(tmp_path):
    """Com o mesmo total em BRL, o hotel_id menor vem primeiro."""
    report = run_report(
        tmp_path,
        [
            {"hotel_id": "H09", "hotel_name": "Hotel I", "amount": "500.00"},
            {"hotel_id": "H02", "hotel_name": "Hotel B", "amount": "500.00"},
            {"hotel_id": "H05", "hotel_name": "Hotel E", "amount": "900.00"},
            {"hotel_id": "H07", "hotel_name": "Hotel G", "amount": "500.00"},
        ],
    )

    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H05", "H02", "H07", "H09"]


def test_ranking_tie_respects_top_limit(tmp_path):
    """O corte do --top acontece depois do desempate."""
    report = run_report(
        tmp_path,
        [
            {"hotel_id": "H03", "amount": "500.00"},
            {"hotel_id": "H01", "amount": "500.00"},
            {"hotel_id": "H02", "amount": "500.00"},
        ],
        top=2,
    )

    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H01", "H02"]


def test_ranking_tie_after_currency_conversion(tmp_path):
    """O empate considera o valor já convertido para BRL (100 USD = 542 BRL)."""
    report = run_report(
        tmp_path,
        [
            {"hotel_id": "H02", "currency": "BRL", "amount": "542.00"},
            {"hotel_id": "H01", "currency": "USD", "amount": "100.00"},
        ],
    )

    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H01", "H02"]
    assert [hotel["total_brl"] for hotel in report["top_hotels"]] == ["542.00", "542.00"]


def test_nights_across_year_boundary(tmp_path):
    """30/12 -> 02/01 são 3 noites; com 2 quartos, 6 noites de quarto."""
    report = run_report(
        tmp_path,
        [
            {
                "checkin_date": "2025-12-30",
                "checkout_date": "2026-01-02",
                "rooms": "2",
                "amount": "600.00",
            }
        ],
    )

    assert report["summary"]["total_room_nights"] == 6
    assert report["summary"]["average_nightly_rate_brl"] == "100.00"
    # by_month usa o mês do check-in, mesmo que o check-out caia em outro ano
    assert report["by_month"] == [
        {"month": "2025-12", "reservations": 1, "room_nights": 6, "total_brl": "600.00"}
    ]


def test_nights_across_leap_day(tmp_path):
    """28/02 -> 01/03 em ano bissexto são 2 noites."""
    report = run_report(
        tmp_path,
        [{"checkin_date": "2024-02-28", "checkout_date": "2024-03-01"}],
    )

    assert report["summary"]["total_room_nights"] == 2


def test_no_confirmed_reservations_yields_zeroed_financials(tmp_path):
    """Sem CONFIRMED: contagens por status preservadas, valores e média em 0.00."""
    report = run_report(
        tmp_path,
        [
            {"status": "CANCELLED", "amount": "500.00"},
            {"status": "NO_SHOW", "amount": "300.00"},
            {"status": "CANCELLED", "amount": "200.00"},
        ],
    )

    assert report["summary"] == {
        "total_reservations": 3,
        "confirmed_reservations": 0,
        "cancelled_reservations": 2,
        "no_show_reservations": 1,
        "total_room_nights": 0,
        "total_amount_brl": "0.00",
        "average_nightly_rate_brl": "0.00",
    }
    assert report["by_month"] == []
    assert report["top_hotels"] == []