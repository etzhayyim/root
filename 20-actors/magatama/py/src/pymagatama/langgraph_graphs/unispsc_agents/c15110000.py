from typing import TypedDict, Annotated, List, Any
from langgraph.graph import StateGraph, END

class MineralProcurementState(TypedDict):
    material_id: str
    purity_check: float
    origin_verified: bool
    compliance_risk: List[str]
    approved: bool

def validate_material(state: MineralProcurementState) -> MineralProcurementState:
    # Specialized logic for mineral purity validation
    if state.get('purity_check', 0) < 0.99:
        state['approved'] = False
    return state

def check_compliance(state: MineralProcurementState) -> MineralProcurementState:
    # Dual-use and sanctions checks
    if not state.get('origin_verified', False):
        state['compliance_risk'].append('Origin Unverified')
    return state

def compile_procurement_graph():
    graph = StateGraph(MineralProcurementState)
    graph.add_node('validate', validate_material)
    graph.add_node('compliance', check_compliance)
    graph.set_entry_point('validate')
    graph.add_edge('validate', 'compliance')
    graph.add_edge('compliance', END)
    return graph.compile()

graph = compile_procurement_graph()