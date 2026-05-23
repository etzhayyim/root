from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity: float
    alloy_certified: bool
    value_threshold_exceeded: bool

def validate_spec(state: ProcurementState):
    print('Validating precious metal purity and composition...')
    return {'alloy_certified': state['purity'] >= 0.99}

def security_check(state: ProcurementState):
    print('Executing high-value goods transit protocols...')
    return {'value_threshold_exceeded': True}

graph = StateGraph(ProcurementState)
graph.add_node('validation', validate_spec)
graph.add_node('security', security_check)
graph.set_entry_point('validation')
graph.add_edge('validation', 'security')
graph.add_edge('security', END)
graph = graph.compile()
