from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalSupplyState(TypedDict):
    supply_id: str
    is_sterile: bool
    compliance_verified: bool

def validate_compliance(state: DentalSupplyState):
    # Business logic for dental regulatory check
    return {'compliance_verified': True}

def update_inventory(state: DentalSupplyState):
    print(f'Syncing {state['supply_id']} to dental ERP')
    return {'compliance_verified': True}

workflow = StateGraph(DentalSupplyState)
workflow.add_node('compliance', validate_compliance)
workflow.add_node('inventory', update_inventory)
workflow.set_entry_point('compliance')
workflow.add_edge('compliance', 'inventory')
workflow.add_edge('inventory', END)
graph = workflow.compile()