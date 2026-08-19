from pathlib import Path
from data_generator.seed import make_faker
import logging
import pandas as pd
from datetime import datetime, timedelta

from data_generator.generate_products import generate_products

logger = logging.getLogger(__name__)

MASTER_SEED = 42
START_DATE = "2026-08-01"
NUM_DAYS = 7 # For now, generate data for 7 days

INITIAL_PRODUCTS=50
DAILY_NEW_PRODUCTS=2

def _write(df: pd.DataFrame, entity: str, date: str, base_dir: Path) -> None:
    out_dir = base_dir / entity
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / f"{date}.parquet", engine="pyarrow", index=False)
    logger.info("wrote entity=%s date=%s rows=%d", entity, date, len(df))

def run(base_dir: Path = Path("data")) -> None:
    all_products = pd.DataFrame(columns=["product_id", "name", "category", "price", "listed_date"])

    product_counter = 0

    start = datetime.strptime(START_DATE, "%Y-%m-%d")

    for day_offset in range(NUM_DAYS):
        date = (start + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        n_new_products = INITIAL_PRODUCTS if day_offset == 0 else DAILY_NEW_PRODUCTS


        # products
        products_fake = make_faker(MASTER_SEED, "products", date)
        new_products = generate_products(n_new_products, product_counter, products_fake, date)
        product_counter += n_new_products
        all_products = pd.concat([all_products, new_products], ignore_index=True)
        _write(new_products, "products", date, base_dir)
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()