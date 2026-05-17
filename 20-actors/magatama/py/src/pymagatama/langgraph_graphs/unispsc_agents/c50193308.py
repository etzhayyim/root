from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OrangeProcessingState(TypedDict):
    batch_id: str
    brix_level: float
    safety_cleared: bool
    inspection_logs: List[str]

def validate_quality(state: OrangeProcessingState):
    state['safety_cleared'] = state['brix_level'] >= 10.0
    state['inspection_logs'].append('Brix quality verification complete')
    return {'safety_cleared': state['safety_cleared']}

def route_by_safety(state: OrangeProcessingState):
    return 'process' if state['safety_cleared'] else 'reject'

graph = StateGraph(OrangeProcessingState)
graph.add_node('validate', validate_quality)
graph.add_node('process', lambda x: {'inspection_logs': x['inspection_logs'] + ['Packaging initiated']})
graph.add_node('reject', lambda x: {'inspection_logs': x['inspection_logs'] + ['Batch rejected']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_safety)
graph.add_edge('process', END)
graph.add_edge('reject', END)
compile_graph = graph.compile()