from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    batch_id: str
    purity: float
    compliant: bool

def validate_purity(state: PharmState):
    state['compliant'] = state['purity'] >= 99.0
    return state

def check_regulatory(state: PharmState):
    print(f'Verifying regulatory compliance for batch {state['batch_id']}')
    return state

graph = StateGraph(PharmState)
graph.add_node('validate', validate_purity)
graph.add_node('regulate', check_regulatory)
graph.add_edge('validate', 'regulate')
graph.add_edge('regulate', END)
graph.set_entry_point('validate')
graph = graph.compile()
