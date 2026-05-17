from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ThiabendazoleState(TypedDict):
    purity: float
    safety_compliant: bool
    validation_logs: List[str]

def validate_purity(state: ThiabendazoleState):
    is_valid = state['purity'] >= 99.0
    return {'validation_logs': [f'Purity check: {is_valid}']}

def check_safety_protocols(state: ThiabendazoleState):
    return {'safety_compliant': True}

graph = StateGraph(ThiabendazoleState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', check_safety_protocols)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()