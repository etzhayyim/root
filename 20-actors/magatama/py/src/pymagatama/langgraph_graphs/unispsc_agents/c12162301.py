from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ResinState(TypedDict):
    spec_requirements: dict
    validation_passed: bool
    compliance_logs: List[str]

def validate_viscosity(state: ResinState):
    visc = state['spec_requirements'].get('viscosity', 0)
    passed = 100 <= visc <= 500
    return {'validation_passed': passed, 'compliance_logs': ['Viscosity check: ' + str(passed)]}

def check_compliance(state: ResinState):
    compliance = state['spec_requirements'].get('msds_ready', False)
    return {'compliance_logs': state['compliance_logs'] + ['MSDS check: ' + str(compliance)]}

graph = StateGraph(ResinState)
graph.add_node('validate', validate_viscosity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
