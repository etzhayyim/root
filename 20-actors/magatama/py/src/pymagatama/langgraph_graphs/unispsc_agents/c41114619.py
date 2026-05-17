from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TesterState(TypedDict):
    spec_requirements: dict
    validation_checklist: List[str]
    is_compliant: bool

def validate_load_capacity(state: TesterState):
    capacity = state['spec_requirements'].get('capacity', 0)
    return {'validation_checklist': ['Capacity Verified'] if capacity > 0 else ['Capacity Invalid']}

def structural_analysis(state: TesterState):
    return {'is_compliant': True}

graph = StateGraph(TesterState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('analyze', structural_analysis)
graph.set_entry_point('validate')
graph.add_edge('validate', 'analyze')
graph.add_edge('analyze', END)
graph = graph.compile()