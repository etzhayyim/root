from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabBeverageState(TypedDict):
    test_parameters: dict
    validation_status: bool
    compliance_check: bool

def validate_purity(state: LabBeverageState):
    state['validation_status'] = state['test_parameters'].get('purity') == 'analytical_grade'
    return state

def verify_compliance(state: LabBeverageState):
    state['compliance_check'] = state['test_parameters'].get('regulatory_status') == 'approved'
    return state

graph = StateGraph(LabBeverageState)
graph.add_node('validate', validate_purity)
graph.add_node('comply', verify_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'comply')
graph.add_edge('comply', END)
graph = graph.compile()
