from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeState(TypedDict):
    spec: dict
    approved: bool

def validate_specs(state: TapeState):
    required = ['tensile_strength', 'thermal_rating']
    all_valid = all(k in state['spec'] for k in required)
    return {'approved': all_valid}

def approval_node(state: TapeState):
    print('Validating fiberglass tape technical specifications...')
    return {'approved': state['approved']}

graph = StateGraph(TapeState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
