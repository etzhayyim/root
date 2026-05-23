from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    purity: float
    compliance: bool
    batch_id: str

def validate_purity(state: PharmaState):
    state['compliance'] = state['purity'] >= 99.0
    return state

def check_regulatory(state: PharmaState):
    print(f'Checking compliance for batch {state['batch_id']}')
    return {'compliance': state['compliance']}

graph = StateGraph(PharmaState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_regulatory', check_regulatory)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_regulatory')
graph.add_edge('check_regulatory', END)
graph = graph.compile()
