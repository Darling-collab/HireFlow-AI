from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hireflow.db import engine, health_check
from sqlalchemy import inspect
print("health:", health_check())
print("dialect:", engine.dialect.name)
print("tables:", ", ".join(sorted(inspect(engine).get_table_names())))
