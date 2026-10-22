from decimal import Decimal
import pytest

from financial_rag.config import AppError
from financial_rag.generation import (
    Claim,
    GrowthCalculation,
    calculate_growth,
    validate_calculation_inputs,
)


@pytest.mark.parametrize(
    "prior,current,expected",
    [
        ("245122", "281724", "14.93"),
        ("100", "120", "20.00"),
        ("100", "80", "-20.00"),
        ("100", "100", "0.00"),
    ],
)
def test_growth_calculation(prior, current, expected):
    assert calculate_growth(prior, current) == Decimal(expected)


@pytest.mark.parametrize("prior", ["0", "-100"])
def test_invalid_baseline(prior):
    with pytest.raises(AppError):
        calculate_growth(prior, "120")


def test_inputs_must_exist_in_cited_evidence():
    claim = Claim(
        text="Derived growth",
        citation_ids=["source-1"],
        calculation=GrowthCalculation(
            prior_value="100",
            current_value="120",
        ),
    )
    evidence = [
        {"id": "source-1", "text": "Revenue was 100 and 120."},
        {"id": "source-2", "text": "Revenue was 999."},
    ]

    validate_calculation_inputs(claim, evidence)

    claim.calculation.current_value = "999"
    with pytest.raises(AppError):
        validate_calculation_inputs(claim, evidence)


@pytest.mark.parametrize(
    "prior,current,accepted",
    [
        ("100", "120", True),
        ("100000000", "120000000", True),
        ("100", "120000000", False),
        ("100000000", "120", False),
        ("100000000", "130000000", False),
    ],
)
def test_explicit_million_conversion(prior, current, accepted):
    claim = Claim(
        text="Derived growth",
        citation_ids=["source-1"],
        calculation=GrowthCalculation(
            prior_value=prior,
            current_value=current,
        ),
    )
    evidence = [{
        "id": "source-1",
        "text": "Revenue was USD 120 million, compared with USD 100 million.",
    }]

    if accepted:
        validate_calculation_inputs(claim, evidence)
        assert calculate_growth(prior, current) == Decimal("20.00")
    else:
        with pytest.raises(AppError):
            validate_calculation_inputs(claim, evidence)
