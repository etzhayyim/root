from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CrystalProcurementState(TypedDict):
    purity_level: float
    structural_verification: bool
    export_control_clearance: bool
    approved: bool

def verify_crystal_quality(state: CrystalProcurementState) -> CrystalProcurementState:
    if state['purity_level'] >= 99.999:
        state['structural_verification'] = True
    return state

def check_export_compliance(state: CrystalProcurementState) -> CrystalProcurementState:
    if state['structural_verification']:
        state['export_control_clearance'] = True
        state['approved'] = True
    return state

graph = StateGraph(CrystalProcurementState)
graph.add_node('verify_quality', verify_crystal_quality)
graph.add_node('check_export', check_export_compliance)
graph.add_edge('verify_quality', 'check_export')
graph.add_edge('check_export', END)
graph.set_entry_point('verify_quality')
graph = graph.compile()
