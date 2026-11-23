"""Steps that put data in front of the system: a table inside the example, or a simulated data set by its id."""
from behave import given

from sim.datasets import DATA_SETS
from sim.generate import OUT, load


# B5T2 Part A: write the step "only these trip requests are received:" here. It reads the example's table
# (context.table) and adds each row to context.deliveries as a trip_requested delivery.


@given("the function fails after it counted {event_id} and receives both requests again")
def step_batch_again(context, event_id):
    """Lambda sends the whole batch again after a failure: the function sees the counted request a second time."""
    done = [d["event_id"] for d in context.deliveries].index(event_id) + 1
    context.deliveries = context.deliveries[:done] + context.deliveries


@given('the simulated data set {sim_id} "{name}"')
def step_data_set(context, sim_id, name):
    assert sim_id in DATA_SETS, f"{sim_id} is not a data set in sim/datasets.py"
    assert DATA_SETS[sim_id]["name"] == name, f'{sim_id} is named "{DATA_SETS[sim_id]["name"]}", not "{name}"'
    context.data_set = context.data_sets[sim_id]
    context.deliveries = context.data_set["deliveries"]


@given("the deliveries of {sim_id}")
def step_deliveries_of(context, sim_id):
    """The deliveries of a generated data set, read from sim/data/<id>/ in the order received. Its _truth/ is not read."""
    assert (OUT / sim_id).exists(), f"sim/data/{sim_id}/ not found: run uv run python -m sim.generate first"
    context.deliveries = load(sim_id)["deliveries"]
