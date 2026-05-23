from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class WashingRackState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: WashingRackState):
    errors = []
    if state['spec_data'].get('load_capacity', 0) <= 0:
        errors.append('Invalid load capacity')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def finalize_order(state: WashingRackState):
    return {'validation_passed': True}

graph = StateGraph(WashingRackState)
graph.add_node('validate', validate_specs)
graph.add_node('finish', finalize_order)
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
