from typing import TypedDict
from langgraph.graph import StateGraph, END

class AntiscalantState(TypedDict):
    concentration: float
    compatibility_check: bool
    approved: bool

def validate_concentration(state: AntiscalantState):
    return {'approved': state['concentration'] > 0.05}

def check_compatibility(state: AntiscalantState):
    return {'compatibility_check': True}

graph = StateGraph(AntiscalantState)
graph.add_node('validate', validate_concentration)
graph.add_node('check', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()