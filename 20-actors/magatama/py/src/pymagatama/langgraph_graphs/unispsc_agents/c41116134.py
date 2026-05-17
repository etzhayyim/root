from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BioReagentState(TypedDict):
    material_id: str
    temp_control_required: bool
    validation_status: str
    compliance_checks: List[str]

def validate_reagent(state: BioReagentState):
    state['validation_status'] = 'Certified' if state.get('temp_control_required') else 'Flagged'
    return state

def check_compliance(state: BioReagentState):
    state['compliance_checks'].append('ISO_13485_Verified')
    return state

graph = StateGraph(BioReagentState)
graph.add_node('validate', validate_reagent)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()