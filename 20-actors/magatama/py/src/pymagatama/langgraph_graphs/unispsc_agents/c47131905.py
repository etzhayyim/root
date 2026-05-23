from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SpillKitState(TypedDict):
    kit_id: str
    contents: List[str]
    compliance_status: bool
    is_hazardous_material: bool

def validate_compliance(state: SpillKitState):
    # Simulate regulatory validation logic
    state['compliance_status'] = len(state['contents']) > 0
    return state

def check_hazmat(state: SpillKitState):
    state['is_hazardous_material'] = True # Default logic for spill kits
    return state

workflow = StateGraph(SpillKitState)
workflow.add_node('validate', validate_compliance)
workflow.add_node('hazmat_check', check_hazmat)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'hazmat_check')
workflow.add_edge('hazmat_check', END)
graph = workflow.compile()
