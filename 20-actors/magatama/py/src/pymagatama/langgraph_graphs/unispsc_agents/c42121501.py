from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    device_id: str
    calibration_compliant: bool
    validation_passed: bool

def validate_specs(state: State):
    state['calibration_compliant'] = True
    return {'validation_passed': True}

def update_inventory(state: State):
    print(f'Inventory record updated for device: {state["device_id"]}')
    return {}

graph = StateGraph(State)
graph.add_node('validate', validate_specs)
graph.add_node('inventory', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph = graph.compile()