from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class GraphiteState(TypedDict):
    purity_level: float
    particle_size: float
    status: str
    validation_log: List[str]

def validate_purity(state: GraphiteState) -> GraphiteState:
    if state['purity_level'] < 95.0:
        state['status'] = 'REJECTED'
        state['validation_log'].append('Low purity: below 95% threshold')
    else:
        state['status'] = 'PASSED'
        state['validation_log'].append('Purity criteria met')
    return state

def check_particle_size(state: GraphiteState) -> GraphiteState:
    if state['particle_size'] > 500:
        state['status'] = 'REJECTED'
        state['validation_log'].append('Particle size exceeds limit')
    return state

builder = StateGraph(GraphiteState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('check_size', check_particle_size)
builder.add_edge('validate_purity', 'check_size')
builder.add_edge('check_size', END)
builder.set_entry_point('validate_purity')
graph = builder.compile()
