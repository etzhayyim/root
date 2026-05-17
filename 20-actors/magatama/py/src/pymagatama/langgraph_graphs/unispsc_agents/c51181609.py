from typing import TypedDict
from langgraph.graph import StateGraph, END

class SodiumIodideState(TypedDict):
    purity: float
    safety_cleared: bool
    storage_temp: float

def validate_specs(state: SodiumIodideState):
    if state['purity'] < 99.0:
        raise ValueError('Purity below chemical grade requirement')
    return {'safety_cleared': True}

def process_hazard_check(state: SodiumIodideState):
    print('Verifying SDS and handling protocols for Sodium Iodide...')
    return {'safety_cleared': True}

graph = StateGraph(SodiumIodideState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', process_hazard_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()