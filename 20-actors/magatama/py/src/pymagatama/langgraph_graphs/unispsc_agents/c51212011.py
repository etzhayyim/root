from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PimpinellaState(TypedDict):
    batch_id: str
    purity_level: float
    moisture_content: float
    is_compliant: bool

def validate_quality(state: PimpinellaState):
    state['is_compliant'] = state['purity_level'] > 0.95 and state['moisture_content'] < 0.12
    return state

def route_by_compliance(state: PimpinellaState):
    return 'process' if state['is_compliant'] else 'reject'

graph = StateGraph(PimpinellaState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': END, 'reject': END})
compiled_graph = graph.compile()