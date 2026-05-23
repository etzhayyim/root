from typing import TypedDict
from langgraph.graph import StateGraph, END

class AprotininState(TypedDict):
    purity: float
    storage_temp: float
    is_certified: bool

def validate_purity(state: AprotininState):
    assert state['purity'] >= 0.98, 'Insufficient purity level for pharmaceutical grade.'
    return {'is_certified': True}

def check_cold_chain(state: AprotininState):
    assert state['storage_temp'] <= 8.0, 'Cold chain requirement violated.'
    return {'is_certified': True}

graph = StateGraph(AprotininState)
graph.add_node('validate', validate_purity)
graph.add_node('chain', check_cold_chain)
graph.add_edge('validate', 'chain')
graph.add_edge('chain', END)
graph.set_entry_point('validate')
app = graph.compile()
