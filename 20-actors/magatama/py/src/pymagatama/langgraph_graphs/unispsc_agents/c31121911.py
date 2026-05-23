from typing import TypedDict
from langgraph.graph import StateGraph, END

class MoldState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: MoldState):
    required = ['material', 'thermal_limit']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validated': len(missing) == 0, 'error_log': missing}

def route_verification(state: MoldState):
    return 'validate' if not state.get('validated') else END

graph = StateGraph(MoldState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
