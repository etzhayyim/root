from langgraph.graph import StateGraph, END
from typing import TypedDict

class RibbonState(TypedDict):
    material: str
    width_mm: float
    color_code: str
    passed_qc: bool

def validate_specs(state: RibbonState):
    state['passed_qc'] = state['width_mm'] > 0 and state['material'] in ['Satin', 'Grosgrain', 'Organza']
    return state

def check_compliance(state: RibbonState):
    return 'passed' if state['passed_qc'] else 'failed'

graph = StateGraph(RibbonState)
graph.add_node('spec_validator', validate_specs)
graph.set_entry_point('spec_validator')
graph.add_edge('spec_validator', END)