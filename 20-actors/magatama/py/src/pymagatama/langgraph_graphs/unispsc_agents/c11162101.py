from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    material_id: str
    purity: float
    status: str
    compliance_report: Sequence[str]

def validate_material(state: MineralState) -> dict:
    status = 'approved' if state['purity'] >= 99.9 else 'rejected'
    return {'status': status, 'compliance_report': [f'Purity check result: {status}']}

def update_inventory(state: MineralState) -> dict:
    return {'compliance_report': ['Inventory recorded in ledger']}

workflow = StateGraph(MineralState)
workflow.add_node('validation', validate_material)
workflow.add_node('inventory', update_inventory)
workflow.add_edge('validation', 'inventory')
workflow.add_edge('inventory', END)
workflow.set_entry_point('validation')
graph = workflow.compile()
