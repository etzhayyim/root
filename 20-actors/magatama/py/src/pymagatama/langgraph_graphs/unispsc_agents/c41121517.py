from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipetterState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_specs(state: PipetterState):
    required = ['Material Compatibility', 'Sterility Status']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state

def route_verification(state: PipetterState):
    return 'validate' if not state.get('is_compliant') else END

graph = StateGraph(PipetterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
