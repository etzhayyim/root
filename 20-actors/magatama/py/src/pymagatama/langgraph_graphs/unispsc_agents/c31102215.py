from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MoldState(TypedDict):
    material_specs: dict
    validation_passed: bool
    compliance_checks: List[str]

def validate_material(state: MoldState):
    purity = state['material_specs'].get('graphite_purity', 0)
    state['validation_passed'] = purity >= 99.0
    state['compliance_checks'].append('Purity Check')
    return state

def check_hazmat(state: MoldState):
    state['compliance_checks'].append('Lead Safety Protocol')
    return state

graph = StateGraph(MoldState)
graph.add_node('validate', validate_material)
graph.add_node('hazmat', check_hazmat)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazmat')
graph.add_edge('hazmat', END)
graph = graph.compile()
