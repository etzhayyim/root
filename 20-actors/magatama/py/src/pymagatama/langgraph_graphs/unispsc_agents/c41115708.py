from langgraph.graph import StateGraph, END
from typing import TypedDict
class HPTLCState(TypedDict):
    specs: dict
    validation_passed: bool
def validate_specs(state: HPTLCState):
    state['validation_passed'] = 'software_compliance_21cfr_part11' in state['specs']
    return state
def check_compliance(state: HPTLCState):
    return 'process_order' if state['validation_passed'] else 'request_revision'
graph = StateGraph(HPTLCState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'process_order': END, 'request_revision': END})
graph.compile()