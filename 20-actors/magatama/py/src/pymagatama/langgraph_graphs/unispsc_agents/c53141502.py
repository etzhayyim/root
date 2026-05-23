from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PinState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: List[str]

def validate_pin_specs(state: PinState):
    errors = []
    if state['spec_data'].get('pin_length_mm', 0) <= 0:
        errors.append('Invalid length')
    return {'validation_passed': len(errors) == 0, 'error_log': errors}

def finalize_procurement(state: PinState):
    return {'validation_passed': True}

graph = StateGraph(PinState)
graph.add_node('validate', validate_pin_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
