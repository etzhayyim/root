from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RehabState(TypedDict):
    specs: dict
    is_compliant: bool
    history: List[str]

def validate_safety(state: RehabState):
    load = state['specs'].get('load_capacity', 0)
    state['is_compliant'] = load > 100
    state['history'].append('Safety check completed')
    return {'is_compliant': state['is_compliant']}

def process_procurement(state: RehabState):
    state['history'].append('Procurement workflow finalized')
    return {'history': state['history']}

graph = StateGraph(RehabState)
graph.add_node('safety_check', validate_safety)
graph.add_node('procurement', process_procurement)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'procurement')
graph.add_edge('procurement', END)
graph = graph.compile()
