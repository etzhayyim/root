from langgraph.graph import StateGraph, END
from typing import TypedDict
class IronProcurementState(TypedDict):
    spec_data: dict
    is_compliant: bool
def validate_safety_specs(state: IronProcurementState):
    required = ['Voltage', 'Safety Certification']
    state['is_compliant'] = all(k in state['spec_data'] for k in required)
    return state
def finalize_order(state: IronProcurementState):
    return {'status': 'approved' if state['is_compliant'] else 'rejected'}
graph = StateGraph(IronProcurementState)
graph.add_node('validate', validate_safety_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()