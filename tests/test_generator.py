"""Covers the three real bugs this project hit during development:
non-reproducible output from hash()/PYTHONHASHSEED in seeding.py, an injection
rate that silently missed its target in generate_customers.py, and a weighted
distribution that silently went uniform in providers.py. All three were only
caught by checking actual measured output instead of reading the code, so
these tests check measured output too instead of relying on remembering to do
that by hand."""

import subprocess
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import pytest
from faker import Faker

from data_generator.generate_customers import generate_customers
from data_generator.generate_orders import generate_orders
from data_generator.providers import OrderStatusProvider
from data_generator.inject_data_quality_issues import (
    inject_duplicate_orders,
    inject_inconsistent_country_codes,
    inject_invalid_amounts,
    inject_malformed_dates,
    inject_missing_customer_ids,
)
from data_generator.seeding import make_faker, make_rng, stable_seed

RATE_TOLERANCE = 0.015  # absolute, e.g. a 5% target must land within 3.5%-6.5%


def test_stable_seed_matches_across_two_python_processes():
    """hash() on strings is randomized per process unless PYTHONHASHSEED is
    fixed. This spawns two real subprocesses to catch that, since a
    single-process test can't."""
    script = "from data_generator.seeding import stable_seed; print(stable_seed(42, 'customers', '2026-08-01'))"
    results = {
        subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=Path(__file__).parent.parent).stdout.strip()
        for _ in range(2)
    }
    assert len(results) == 1, f"stable_seed produced different values across processes: {results}"


def test_generate_customers_is_deterministic():
    fake_a = make_faker(42, "customers", "2026-08-01")
    run_a = generate_customers(50, 0, fake_a, "2026-08-01")

    fake_b = make_faker(42, "customers", "2026-08-01")
    run_b = generate_customers(50, 0, fake_b, "2026-08-01")

    pd.testing.assert_frame_equal(run_a, run_b)


def test_generate_customers_independent_of_other_entities_seeded_first():
    """A shared, class-level Faker.seed() means calling another entity's
    generator first changes this entity's output. make_faker uses an
    independent seed_instance per entity, so that must not happen here."""
    fake_alone = make_faker(42, "customers", "2026-08-01")
    run_alone = generate_customers(10, 0, fake_alone, "2026-08-01")

    # simulate "something else ran first" by drawing from an unrelated Faker
    # instance before generating customers
    from data_generator.seeding import make_faker as _mf

    _ = _mf(42, "products", "2026-08-01").name()  # unrelated draw, different entity/seed
    fake_after_other_draw = make_faker(42, "customers", "2026-08-01")
    run_after = generate_customers(10, 0, fake_after_other_draw, "2026-08-01")

    pd.testing.assert_frame_equal(run_alone, run_after)


def _make_orders(n=2000):
    customers = generate_customers(300, 0, make_faker(1, "customers", "2026-08-01"), "2026-08-01")
    return generate_orders(n, 0, customers, "2026-08-01", make_faker(1, "orders", "2026-08-01"), make_rng(1, "orders", "2026-08-01"))


def test_duplicate_orders_rate():
    orders = _make_orders()
    result = inject_duplicate_orders(orders, 0.05, make_rng(2, "dup", "x"))
    assert abs(result["order_id"].duplicated().mean() - 0.05) < RATE_TOLERANCE


def test_missing_customer_id_rate():
    orders = _make_orders()
    result = inject_missing_customer_ids(orders, 0.02, make_rng(2, "missing", "x"))
    assert abs(result["customer_id"].isna().mean() - 0.02) < RATE_TOLERANCE


def test_malformed_date_rate():
    orders = _make_orders()
    result = inject_malformed_dates(orders, 0.01, make_rng(2, "dates", "x"))
    bad = pd.to_datetime(result["order_date"], errors="coerce").isna()
    assert abs(bad.mean() - 0.01) < RATE_TOLERANCE


def test_invalid_amount_rate():
    orders = _make_orders()
    orders["total_amount"] = 100.0  # inject needs a real amount column present
    result = inject_invalid_amounts(orders, 0.01, make_rng(2, "amounts", "x"))
    bad = (result["total_amount"] < 0) | result["total_amount"].isna()
    assert abs(bad.mean() - 0.01) < RATE_TOLERANCE


def test_inconsistent_country_code_rate_reachable():
    """Regression test for a real bug: fake.country_code() drew uniformly from
    ~195 countries, which made a 3% injection rate structurally unreachable,
    since the eligible pool (customers already coded as one of six corruptible
    countries) was far smaller than 3% of the population to begin with.
    generate_customers needs a concentrated enough distribution for this rate
    to actually be achievable."""
    customers = generate_customers(1000, 0, make_faker(3, "customers", "2026-08-01"), "2026-08-01")
    result = inject_inconsistent_country_codes(customers, 0.03, make_rng(3, "country", "x"))
    valid = {"US", "GB", "DE", "FR", "CA", "JP"}
    inconsistent_rate = (~result["country_code"].isin(valid)).mean()
    assert abs(inconsistent_rate - 0.03) < RATE_TOLERANCE, (
        f"got {inconsistent_rate:.1%}. If this is ~0%, the eligible-pool bug is back: "
        f"check generate_customers' country distribution isn't uniform again"
    )


def test_order_status_provider_is_actually_weighted():
    """Regression test for a real bug: a custom provider method written as
    `self.random_element(self._weights)` looks correct and even passed a
    manual spot-check, but silently ignored the weights. BaseProvider's
    __use_weighting__ defaults to False, and self inside a custom provider is
    the provider instance, not the top-level Faker object, which behaves
    differently. Without __use_weighting__ = True set on the provider class,
    'delivered' (75% target) comes out at roughly the same rate as every other
    status (~20% each) instead."""
    fake = Faker()
    fake.add_provider(OrderStatusProvider)
    fake.seed_instance(1)

    counts = Counter(fake.order_status() for _ in range(3000))
    delivered_rate = counts["delivered"] / 3000
    assert abs(delivered_rate - 0.75) < RATE_TOLERANCE, (
        f"'delivered' landed at {delivered_rate:.1%}, not ~75%. If this is ~20%, "
        f"weighting silently isn't being applied: check __use_weighting__ = True "
        f"is set on the provider class"
    )
