from typing import TypedDict
from langgraph.graph import StateGraph, END

class PinState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_pin_specs(state: PinState):
    specs = state['spec_data']
    errors = []
    if 'hardness' not in specs: errors.append('Missing hardness rating')
    if 'diameter' not in specs: errors.append('Missing diameter')
    return {'validated': len(errors) == 0, 'error_log': errors}

graph = StateGraph(PinState)
graph.add_node('validate', validate_pin_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()