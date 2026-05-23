from typing import TypedDict
from langgraph.graph import StateGraph, END
class KineticState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_check: bool
def validate_specs(state: KineticState):
    state['validation_passed'] = all(k in state['specs'] for k in ['torque', 'rpm'])
    print('Validating mechanical specs...')
    return state
def check_export_compliance(state: KineticState):
    state['compliance_check'] = state.get('is_dual_use', False)
    print('Checking export controls...')
    return state
graph = StateGraph(KineticState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
