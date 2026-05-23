from typing import TypedDict, Annotated, Sequence, List
import operator
from langgraph.graph import StateGraph, END

class MetalProcurementState(TypedDict):
    commodity_code: str
    purity: float
    compliance_checks: Annotated[List[str], operator.add]
    is_approved: bool

def validate_purity(state: MetalProcurementState):
    # Business logic for industrial metal purity validation
    if state['purity'] >= 99.9:
        return {'compliance_checks': ['High purity verified']}
    return {'compliance_checks': ['Purity insufficient']}

def check_export_controls(state: MetalProcurementState):
    # Dual-use / Sanctions screening
    return {'compliance_checks': ['Dual-use screening complete']}

def finalize_procurement(state: MetalProcurementState):
    # Final decision logic
    is_approved = 'High purity verified' in state['compliance_checks']
    return {'is_approved': is_approved}

graph = StateGraph(MetalProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('export', check_export_controls)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
