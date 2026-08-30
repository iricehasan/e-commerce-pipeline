import numpy as np
import pandas as pd

# orders related issues

def inject_duplicate_orders(orders_df: pd.DataFrame, rate: float, rng: np.random.Generator) -> pd.DataFrame:
    """Duplicates existing rows under their original order_id. Exercises natural-key
    dedup specifically, not content-based or fuzzy duplicate detection, which would
    need its own injector."""
    n_dupes = int(len(orders_df) * rate)
    if n_dupes == 0:
        return orders_df
    dupe_rows = orders_df.sample(n=n_dupes, random_state=int(rng.integers(0, 2**31 - 1)))
    return pd.concat([orders_df, dupe_rows], ignore_index=True)


def inject_missing_customer_ids(orders_df: pd.DataFrame, rate: float, rng: np.random.Generator) -> pd.DataFrame:
    df = orders_df.copy()
    idx = df.sample(frac=rate, random_state=int(rng.integers(0, 2**31 - 1))).index
    df.loc[idx, "customer_id"] = None
    return df


def inject_malformed_dates(orders_df: pd.DataFrame, rate: float, rng: np.random.Generator) -> pd.DataFrame:
    """Uses a fixed set of corruption modes instead of arbitrary bad strings, so
    downstream quarantine logic can be tested against known failure cases."""
    df = orders_df.copy()
    idx = df.sample(frac=rate, random_state=int(rng.integers(0, 2**31 - 1))).index
    corruptions = ["2026-13-45", "not-a-date", "02/30/2026", ""]
    for i in idx:
        df.loc[i, "order_date"] = rng.choice(corruptions)
    return df


def inject_invalid_amounts(orders_df: pd.DataFrame, rate: float, rng: np.random.Generator) -> pd.DataFrame:
    """Covers two invalid shapes on purpose: negative amounts, which could be a
    misclassified refund, and null amounts, which are genuinely missing. Downstream
    cleaning may need to handle these two cases differently, so both are
    represented."""
    df = orders_df.copy()
    idx = df.sample(frac=rate, random_state=int(rng.integers(0, 2**31 - 1))).index
    for i in idx:
        current = df.loc[i, "total_amount"]
        df.loc[i, "total_amount"] = rng.choice([-abs(current) if pd.notna(current) else -1.0, None])
    return df


# customers related issues

_COUNTRY_CODE_VARIANTS = {
    "US": ["USA", "United States", "us"],
    "GB": ["UK", "United Kingdom", "gb"],
    "DE": ["Germany", "de"],
    "FR": ["France", "fr"],
    "CA": ["Canada", "ca"],
    "JP": ["Japan", "jp"],
}


def inject_inconsistent_country_codes(customers_df: pd.DataFrame, rate: float, rng: np.random.Generator) -> pd.DataFrame:
    """Produces variant spellings/casings that a normalization mapping can recover,
    rather than garbage a validator would just reject. Deliberately a different
    failure shape from the other injectors, since a strict validator would drop
    otherwise-good rows instead of allowing them to be corrected."""
    df = customers_df.copy()
    eligible = df[df["country_code"].isin(_COUNTRY_CODE_VARIANTS.keys())]
    if eligible.empty:
        return df
    idx = eligible.sample(frac=rate, random_state=int(rng.integers(0, 2**31 - 1))).index
    for i in idx:
        code = df.loc[i, "country_code"]
        df.loc[i, "country_code"] = rng.choice(_COUNTRY_CODE_VARIANTS[code])
    return df
