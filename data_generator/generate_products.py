import pandas as pd
from faker import Faker

from data_generator.providers import ProductCategoryProvider


def generate_products(n: int, counter: int, fake: Faker, listed_date: str) -> pd.DataFrame:
    fake.add_provider(ProductCategoryProvider)
    rows = []
    for i in range(n):
        rows.append(
            {
                "product_id": f"prod_{counter + i:06d}",
                "name": fake.catch_phrase(),
                "category": fake.product_category(),
                "price": float(fake.pydecimal(left_digits=3, right_digits=2, min_value=5, max_value=999)),
                "listed_date": listed_date,
            }
        )
    return pd.DataFrame(rows)