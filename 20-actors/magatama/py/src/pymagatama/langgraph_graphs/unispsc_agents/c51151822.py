from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcureState(TypedDict):
    batch_id: str
    purity_level: float
    gmp_status: bool
    is_approved: bool

def validate_pharmaceutical(state: ProcureState):
    state['is_approved'] = state['purity_level'] >= 99.0 and state['gmp_status'] is True
    return state

def process_logistics(state: ProcureState):
    print(f'Processing batch {state['batch_id']} for cold chain logistics')
    return state

graph = StateGraph(ProcureState)
graph.add_node('validate', validate_pharmaceutical)
graph.add_node('logistics', process_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()