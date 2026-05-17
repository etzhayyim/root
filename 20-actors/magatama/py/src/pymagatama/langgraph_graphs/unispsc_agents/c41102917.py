from typing import TypedDict
from langgraph.graph import StateGraph, END
class ValidationState(TypedDict):
    blade_type: str
    iso_compliant: bool
    passed_safety_check: bool
def check_compliance(state: ValidationState):
    state['iso_compliant'] = True if state.get('iso_compliant') else False
    return {'iso_compliant': state['iso_compliant']}
def verify_blade(state: ValidationState):
    state['passed_safety_check'] = state['blade_type'] in ['tungsten', 'steel']
    return {'passed_safety_check': state['passed_safety_check']}
graph = StateGraph(ValidationState)
graph.add_node('compliance', check_compliance)
graph.add_node('safety', verify_blade)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()