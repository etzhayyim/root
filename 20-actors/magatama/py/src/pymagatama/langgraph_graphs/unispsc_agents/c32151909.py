from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ConnectorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_status: List[str]

def validate_specs(state: ConnectorState):
    specs = state['spec_data']
    passed = 'IP_Rating' in specs and 'Termination_Method' in specs
    return {'validation_passed': passed}

def check_compliance(state: ConnectorState):
    return {'compliance_status': ['RoHS_Compliant', 'CE_Marked']}

graph = StateGraph(ConnectorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()