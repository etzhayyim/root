from typing import TypedDict
from langgraph.graph import StateGraph, END

class PulpProcessState(TypedDict):
    pulp_source: str
    quality_score: float
    is_approved: bool

def validate_specs(state: PulpProcessState):
    state['is_approved'] = True if state['quality_score'] > 0.8 else False
    return state

def route_by_quality(state: PulpProcessState):
    return 'process_batch' if state['is_approved'] else 'reject_batch'

graph = StateGraph(PulpProcessState)
graph.add_node('validate', validate_specs)
graph.add_node('process_batch', lambda x: x)
graph.add_node('reject_batch', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_quality)
graph.add_edge('process_batch', END)
graph.add_edge('reject_batch', END)
graph = graph.compile()