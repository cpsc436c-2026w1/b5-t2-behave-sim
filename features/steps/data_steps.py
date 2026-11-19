"""Steps that put data in front of the system: a table inside the example, or a simulated data set by its id."""
from behave import given

from sim.datasets import DATA_SETS


@given("only these trip requests are received:")
def step_requests_table(context):
    for row in context.table:
        delivery = dict(zip(context.table.headings, row.cells))
        delivery["event_type"] = "trip_requested"
        context.deliveries.append(delivery)


@given('the simulated data set {sim_id} "{name}"')
def step_data_set(context, sim_id, name):
    assert sim_id in DATA_SETS, f"{sim_id} is not a data set in sim/datasets.py"
    assert DATA_SETS[sim_id]["name"] == name, f'{sim_id} is named "{DATA_SETS[sim_id]["name"]}", not "{name}"'
    context.data_set = context.data_sets[sim_id]
    context.deliveries = context.data_set["deliveries"]
