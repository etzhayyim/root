from typing import TypedDict
from langgraph.graph import StateGraph, END

class GrapeJuiceState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_purity(state: GrapeJuiceState):
    state['validation_passed'] = state['spec_data'].get('brix_level', 0) >= 15
    return state

def check_logistics(state: GrapeJuiceState):
    state['compliance_report'] = 'Logistics confirmed' if 'storage_temperature_requirements' in state['spec_data'] else 'Logistics missing'
    return state

graph = StateGraph(GrapeJuiceState)
graph.add_node('validate', validate_purity)
graph.add_node('logistics', check_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()