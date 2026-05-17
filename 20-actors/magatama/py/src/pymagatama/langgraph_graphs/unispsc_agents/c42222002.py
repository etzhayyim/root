from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    approved: bool

def validate_flow_specs(state: PumpState):
    accuracy = state['spec_data'].get('flow_accuracy', 0)
    if accuracy <= 2.0:
        state['validation_results'].append('Accuracy validated')
    else:
        state['validation_results'].append('Accuracy failed')
    return state

def check_compliance(state: PumpState):
    if 'ISO_13485' in state['spec_data'].get('certs', []):
        state['approved'] = True
    return state

graph = StateGraph(PumpState)
graph.add_node('validate', validate_flow_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()