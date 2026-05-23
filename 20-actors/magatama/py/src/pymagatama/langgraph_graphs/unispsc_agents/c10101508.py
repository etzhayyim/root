from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MiningState(TypedDict):
    equipment_id: str
    inspection_status: str
    compliance_checks: List[str]
    approval_required: bool

def validate_mining_spec(state: MiningState):
    # Simulate spec validation logic for heavy machinery
    state['compliance_checks'].append('SafetyStandard_ISO_9001')
    state['inspection_status'] = 'Pending'
    return state

def check_export_controls(state: MiningState):
    # Dual-use export control check
    state['approval_required'] = True
    return state

workflow = StateGraph(MiningState)
workflow.add_node('validate', validate_mining_spec)
workflow.add_node('export_check', check_export_controls)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'export_check')
workflow.add_edge('export_check', END)

graph = workflow.compile()
