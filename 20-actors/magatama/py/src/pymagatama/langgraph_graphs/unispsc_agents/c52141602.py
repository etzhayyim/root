from typing import TypedDict
from langgraph.graph import StateGraph, END

class DryerProcurementState(TypedDict):
    model_number: str
    energy_rating: str
    is_compliant: bool

def validate_compliance(state: DryerProcurementState):
    state['is_compliant'] = state['energy_rating'] in ['A+++', 'A++']
    return state

def routing_logic(state: DryerProcurementState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

workflow = StateGraph(DryerProcurementState)
workflow.add_node('validate', validate_compliance)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', routing_logic, {'compliant': END, 'manual_review': END})
graph = workflow.compile()
