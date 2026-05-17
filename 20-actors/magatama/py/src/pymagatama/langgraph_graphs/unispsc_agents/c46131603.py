from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BoosterState(TypedDict):
    specs: dict
    validation_checks: List[str]
    is_cleared: bool

def validate_tech(state: BoosterState):
    compliance = state['specs'].get('compliance', 'none')
    status = True if compliance == 'ITAR' else False
    return {'validation_checks': ['ITAR_check'], 'is_cleared': status}

def integration(state: BoosterState):
    return {'validation_checks': state['validation_checks'] + ['integration_ready']}

graph = StateGraph(BoosterState)
graph.add_node('validate', validate_tech)
graph.add_node('integrate', integration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integrate')
graph.add_edge('integrate', END)
graph = graph.compile()