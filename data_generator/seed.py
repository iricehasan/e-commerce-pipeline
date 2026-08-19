import hashlib
from faker import Faker
import numpy as np

"""
Shared, stable seed for reproducing the same data for every generator module.

Using hashlib instead of default hash function since 
hash function is randomized per process.
"""
def stable_seed(*parts: object) -> int:
    # "|" prevents different inputs from colliding into 
    # the same string once joined.
    key = "|".join(str(p) for p in parts).encode("utf-8")
    return int(hashlib.sha256(key).hexdigest(), 16) % (2**32)

def make_faker(master_seed: int, entity: str, date: str) -> Faker:
    fake = Faker()
    fake.seed_instance(stable_seed(master_seed, entity, date))
    return fake

def make_rng(master_seed: int, entity: str, date: str) -> np.random.Generator:
    """Using Pareto Distribution for orders"""
    return np.random.default_rng(stable_seed(master_seed, entity, date, "numpy"))