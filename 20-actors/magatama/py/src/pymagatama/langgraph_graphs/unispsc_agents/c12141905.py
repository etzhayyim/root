from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CarbonState(TypedDict):
    purity: float
    particle_size: float
    is_approved: bool
    history: List[str]

def validate_purity(state: CarbonState):
    approval = state['purity'] >= 99.9
    return {'is_approved': approval, 'history': state['history'] + ['purity_validated']}

def check_size(state: CarbonState):
    status = 'size_within_spec' if state['particle_size'] < 5.0 else 'size_too_large'
    return {'history': state['history'] + [status]}

graph = StateGraph(CarbonState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_size', check_size)
graph.add_edge('validate_purity', 'check_size')
graph.add_edge('check_size', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()