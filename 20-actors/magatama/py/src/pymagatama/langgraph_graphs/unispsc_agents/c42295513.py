from typing import TypedDict
from langgraph.graph import StateGraph, END
class SurgicalMeshState(TypedDict):
    material_id: str
    regulatory_docs: list
    is_compliant: bool
def validate_compliance(state: SurgicalMeshState):
    state['is_compliant'] = len(state['regulatory_docs']) > 0
    return 'compliant' if state['is_compliant'] else 'reject'
def notify_procurement(state: SurgicalMeshState):
    print('Procurement review required for high-risk medical material.')
    return 'end'
workflow = StateGraph(SurgicalMeshState)
workflow.add_node('validate', validate_compliance)
workflow.add_node('notify', notify_procurement)
workflow.add_edge('validate', 'notify')
workflow.add_edge('notify', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
