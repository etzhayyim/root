from typing import TypedDict
from langgraph.graph import StateGraph, END

class XylazineProcurementState(TypedDict):
    purity: float
    license_valid: bool
    compliance_cleared: bool

def validate_regulatory_compliance(state: XylazineProcurementState):
    # Regulatory logic for controlled substances
    state['compliance_cleared'] = state['license_valid'] and (state['purity'] >= 99.0)
    return state

workflow = StateGraph(XylazineProcurementState)
workflow.add_node('compliance', validate_regulatory_compliance)
workflow.set_entry_point('compliance')
workflow.add_edge('compliance', END)
graph = workflow.compile()