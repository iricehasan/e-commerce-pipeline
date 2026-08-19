# Project

## `data_generator/`

Synthetic e-commerce data (customers, orders, ...) with deliberately injected data quality issues. Has its own venv, separate from the
pipeline.

### Setup

Run from inside `data_generator/`

```
cd data_generator
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Running it

```
cd ..                       # back to e-commerce-pipeline/, venv still active
python3 -m data_generator.run
```
