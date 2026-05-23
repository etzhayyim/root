from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeedMachineState(TypedDict):
    specs: dict
    validation_status: bool
    error_log: list

def validate_specs(state: WeedMachineState):
    required = ['engine_power', 'safety_rating']
    missing = [f for f in required if f not in state['specs']]
    return {'validation_status': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: WeedMachineState):
    return 'validate' if not state['validation_status'] else END

graph = StateGraph(WeedMachineState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
