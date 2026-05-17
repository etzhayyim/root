from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalProcurementState(TypedDict):
    purity: float
    particle_size: float
    compliance_docs: List[str]
    status: str

def validate_metal_specs(state: MetalProcurementState) -> MetalProcurementState:
    if state['purity'] >= 99.99:
        state['status'] = 'CERTIFIED'
    else:
        state['status'] = 'REJECTED_PURITY_TOO_LOW'
    return state

def check_dangerous_goods_export(state: MetalProcurementState) -> MetalProcurementState:
    if 'MSDS' in state['compliance_docs']:
        state['status'] = 'EXPORT_CLEARANCE_PENDING'
    else:
        state['status'] = 'MISSING_COMPLIANCE_DOCS'
    return state

graph = StateGraph(MetalProcurementState)
graph.add_node('validate', validate_metal_specs)
graph.add_node('compliance', check_dangerous_goods_export)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()