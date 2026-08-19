from pathlib import Path
from data_generator.seed import make_faker
import logging

logger = logging.getLogger(__name__)

MASTER_SEED = 42
START_DATE = "2026-08-01"

def run(base_dir: Path = Path("data")) -> None:
    pass

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run()