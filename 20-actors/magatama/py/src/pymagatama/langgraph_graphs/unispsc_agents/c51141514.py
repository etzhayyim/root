from typing import TypedDict
from langgraph.graph import StateGraph, END

class ZonisamideState(TypedDict):
    batch_id: str
    purity: float
    compliance_ok: bool

def validate_purity(state: ZonisamideState):
    state['compliance_ok'] = state['purity'] >= 99.0
    return state

def log_batch(state: ZonisamideState):
    print(f'Processing batch {state['batch_id']} - Valid: {state['compliance_ok']}')
    return state

graph = StateGraph(ZonisamideState)
graph.add_node('validate', validate_purity)
graph.add_node('log', log_batch)
graph.set_entry_point('validate')
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph = graph.compile()