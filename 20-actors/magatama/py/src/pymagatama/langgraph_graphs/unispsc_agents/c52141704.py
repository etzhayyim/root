from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RazorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: RazorState) -> RazorState:
    required = ['IPX', 'PSE_Certification']
    errors = [f'Missing {f}' for f in required if f not in state['spec_data']]
    state['validation_errors'] = errors
    state['is_compliant'] = len(errors) == 0
    return state

def generate_summary(state: RazorState) -> RazorState:
    print(f'Compliance status: {state['is_compliant']}')
    return state

graph = StateGraph(RazorState)
graph.add_node('validate', validate_specs)
graph.add_node('summary', generate_summary)
graph.set_entry_point('validate')
graph.add_edge('validate', 'summary')
graph.add_edge('summary', END)
graph = graph.compile()
