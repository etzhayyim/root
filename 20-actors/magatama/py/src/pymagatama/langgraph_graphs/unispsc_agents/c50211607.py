from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material: str
    compliance_docs: List[str]
    approved: bool

def validate_cigarette_materials(state: ProcurementState):
    # Perform specialized validation for tobacco-related safety specs
    is_compliant = 'ISO_Standard' in state['compliance_docs']
    return {'approved': is_compliant}

workflow = StateGraph(ProcurementState)
workflow.add_node('validation', validate_cigarette_materials)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
