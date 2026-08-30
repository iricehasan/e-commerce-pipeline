from pathlib import Path
from data_generator.seed import make_faker, make_rng
import logging
import pandas as pd
from datetime import datetime, timedelta

from data_generator.generate_products import generate_products
from data_generator.generate_customers import generate_customers
from data_generator.generate_orders import generate_orders
from data_generator.generate_order_items import generate_order_items, compute_order_totals
from data_generator.generate_payments import generate_payments
from data_generator.generate_events import generate_events

from data_generator.inject_data_quality_issues import (
    inject_duplicate_orders,
    inject_missing_customer_ids,
    inject_malformed_dates,
    inject_invalid_amounts,
    inject_inconsistent_country_codes
)

logger = logging.getLogger(__name__)

MASTER_SEED = 42
START_DATE = "2026-08-01"
NUM_DAYS = 7 # For now, generate data for 7 days

INITIAL_PRODUCTS=50
DAILY_NEW_PRODUCTS=2

INITIAL_CUSTOMERS=200
DAILY_NEW_CUSTOMERS=8

DAILY_ORDERS = 150

DAILY_EVENTS = 1200


ISSUE_RATES = {
    "duplicate_orders": 0.05,
    "missing_customer_ids": 0.02,
    "inconsistent_country_codes": 0.03,
    "malformed_dates": 0.01,
    "invalid_amounts": 0.01,
}

def _write(df: pd.DataFrame, entity: str, date: str, base_dir: Path) -> None:
    out_dir = base_dir / entity
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / f"{date}.parquet", engine="pyarrow", index=False)
    logger.info("wrote entity=%s date=%s rows=%d", entity, date, len(df))

def run(base_dir: Path = Path("data")) -> None:
    all_products = pd.DataFrame(columns=["product_id", "name", "category", "price", "listed_date"])
    all_customers = pd.DataFrame(columns=["customer_id", "name", "email", "country_code", "signup_date"])
    
    product_counter = 0
    customer_counter = 0
    order_counter = 0
    item_counter = 0
    payment_counter = 0
    event_counter = 0

    start = datetime.strptime(START_DATE, "%Y-%m-%d")

    for day_offset in range(NUM_DAYS):
        date = (start + timedelta(days=day_offset)).strftime("%Y-%m-%d")
        n_new_products = INITIAL_PRODUCTS if day_offset == 0 else DAILY_NEW_PRODUCTS
        n_new_customers = INITIAL_CUSTOMERS if day_offset == 0 else DAILY_NEW_CUSTOMERS

        # products
        products_fake = make_faker(MASTER_SEED, "products", date)
        new_products = generate_products(n_new_products, product_counter, products_fake, date)
        product_counter += n_new_products
        all_products = pd.concat([all_products, new_products], ignore_index=True)
        _write(new_products, "products", date, base_dir)

        # customers
        customers_fake = make_faker(MASTER_SEED, "customers", date)
        new_customers = generate_customers(n_new_customers, customer_counter, customers_fake, date)
        customer_counter += n_new_customers
        all_customers = pd.concat([all_customers, new_customers], ignore_index=True)
        _write(new_customers, "customers", date, base_dir)

        # orders
        orders_fake = make_faker(MASTER_SEED, "orders", date)
        orders_rng = make_rng(MASTER_SEED, "orders", date)
        orders = generate_orders(DAILY_ORDERS, order_counter, all_customers, date, orders_fake, orders_rng)
        order_counter += DAILY_ORDERS

        # order items
        items_rng = make_rng(MASTER_SEED, "order_items", date)
        order_items = generate_order_items(orders, all_products, item_counter, orders_fake, items_rng)
        item_counter += len(order_items)
        orders = compute_order_totals(orders, order_items)

        # order related issues after totals are computed
        issues_rng = make_rng(MASTER_SEED, "orders_issues", date)
        orders = inject_duplicate_orders(orders, ISSUE_RATES["duplicate_orders"], issues_rng)
        orders = inject_missing_customer_ids(orders, ISSUE_RATES["missing_customer_ids"], issues_rng)
        orders = inject_malformed_dates(orders, ISSUE_RATES["malformed_dates"], issues_rng)
        orders = inject_invalid_amounts(orders, ISSUE_RATES["invalid_amounts"], issues_rng)
        
        _write(orders, "orders", date, base_dir)
        _write(order_items, "order_items", date, base_dir)

        # payments
        payments_fake = make_faker(MASTER_SEED, "payments", date)
        # payments reference orders BEFORE issue injection
        # since payments should exist for genuine orders not duplicate ones etc.
        clean_orders_for_payment = orders.drop_duplicates(subset="order_id").dropna(subset=["total_amount"])
        payments = generate_payments(clean_orders_for_payment, payment_counter, payments_fake)
        payment_counter += len(payments)
        _write(payments, "payments", date, base_dir)

        # events
        events_fake = make_faker(MASTER_SEED, "events", date)
        events_rng = make_rng(MASTER_SEED, "events", date)
        events = generate_events(DAILY_EVENTS, event_counter, all_customers, date, events_fake, events_rng)
        event_counter += DAILY_EVENTS
        _write(events, "events", date, base_dir)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()