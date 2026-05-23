from typing import TypedDict
from langgraph.graph import StateGraph, END

class LoomState(TypedDict):
    loom_id: str
    validation_score: float
    status: str

def validate_specs(state: LoomState):
    # Simulated automated validation check for looper looms
    valid = state.get('loom_id') is not None
    return {'validation_score': 1.0 if valid else 0.0, 'status': 'valid' if valid else 'error'}

def approval_check(state: LoomState):
    return 'approved' if state['validation_score'] >= 1.0 else 'rejected'

graph = StateGraph(LoomState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
