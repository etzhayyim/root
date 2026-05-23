from typing import TypedDict
from langgraph.graph import StateGraph, END

class KilnState(TypedDict):
    temp_rating: float
    volume: float
    is_compliant: bool

def validate_specs(state: KilnState):
    state['is_compliant'] = state['temp_rating'] >= 1200
    return state

def approval_node(state: KilnState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(KilnState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
