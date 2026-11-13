import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hireflow.db import init_db, seed_demo_data, seed_status_dictionary
init_db(); seed_status_dictionary(); seed_demo_data(); print("HireFlow database initialized")
