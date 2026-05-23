from typing import TypedDict
from langgraph.graph import StateGraph, END

class EbuliometerState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: EbuliometerState):
    required = ['calibration_date', 'pressure_rating']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validated': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: EbuliometerState):
    return 'validate' if not state['validated'] else END

graph = StateGraph(EbuliometerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
