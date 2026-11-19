"""Setup that behave runs around the examples. Checkpoint 2 material: on Monday features/steps/ is empty."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "src")]

from sim.datasets import DATA_SETS          # noqa: E402
from sim.generate import generate, load     # noqa: E402


def before_all(context):
    """Write every data set once a run (the seed is fixed, so the files are the same each time) and load it by id."""
    context.data_sets = {}
    for sim_id in DATA_SETS:
        generate(sim_id)
        context.data_sets[sim_id] = load(sim_id)


def before_scenario(context, scenario):
    context.deliveries = []                 # every example starts without data: "only these trip requests"
