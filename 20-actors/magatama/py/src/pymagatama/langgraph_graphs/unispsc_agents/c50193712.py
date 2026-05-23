from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodProcurementState(TypedDict):
    item_name: str
    expiry_date: str
    compliance_docs: list
    status: str

def validate_food_safety(state: FoodProcurementState):
    print(f'Validating compliance for {state['item_name']}')
    return {'status': 'CERTIFIED' if 'HACCP' in state['compliance_docs'] else 'REJECTED'}

def update_inventory(state: FoodProcurementState):
    print(f'Updating inventory for {state['item_name']} expiring on {state['expiry_date']}')
    return {'status': 'IN_STOCK'}

graph = StateGraph(FoodProcurementState)
graph.add_node('validate', validate_food_safety)
graph.add_node('inventory', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
app = graph.compile()
