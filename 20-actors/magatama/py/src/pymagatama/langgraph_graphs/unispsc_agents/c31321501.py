from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_materials(state: ProcurementState):
    alloy = state['specs'].get('alloy_grade')
    state['validation_passed'] = alloy in ['6061-T6', '7075-T6']
    return state

def check_weld_integrity(state: ProcurementState):
    if state.get('validation_passed'):
        state['compliance_report'] = 'Weld structural integrity verified'
    else:
        state['compliance_report'] = 'Weld structural integrity verification failed'
    return state

graph = StateGraph(ProcurementState)
graph.add_node('verify', validate_materials)
graph.add_node('weld_check', check_weld_integrity)
graph.set_entry_point('verify')
graph.add_edge('verify', 'weld_check')
graph.add_edge('weld_check', END)
graph = graph.compile()