from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FacilityState(TypedDict):
    facility_id: str
    compliance_docs: List[str]
    is_verified: bool

def validate_compliance(state: FacilityState):
    state['is_verified'] = len(state['compliance_docs']) >= 3
    return state

def check_staffing(state: FacilityState):
    print(f'Checking staffing levels for facility: {state['facility_id']}')
    return state

workflow = StateGraph(FacilityState)
workflow.add_node('compliance_check', validate_compliance)
workflow.add_node('staffing_check', check_staffing)
workflow.set_entry_point('compliance_check')
workflow.add_edge('compliance_check', 'staffing_check')
workflow.add_edge('staffing_check', END)
graph = workflow.compile()
