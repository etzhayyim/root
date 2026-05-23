from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TillingMachineState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: TillingMachineState):
    errors = []
    if state['specs'].get('prower_output_kw', 0) <= 0:
        errors.append('Invalid power output')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def safety_check(state: TillingMachineState):
    if 'safety_certification_standards' not in state['specs']:
        return {'validation_errors': state['validation_errors'] + ['Missing safety certs']}
    return {}

graph = StateGraph(TillingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
