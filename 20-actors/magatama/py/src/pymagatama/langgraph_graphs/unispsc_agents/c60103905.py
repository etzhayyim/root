from typing import TypedDict
from langgraph.graph import StateGraph, END

class CultureKitState(TypedDict):
    kit_id: str
    expiry_date: str
    storage_temp: float
    status: str

def validate_storage(state: CultureKitState):
    if state['storage_temp'] > 8.0:
        return {'status': 'REJECTED_TEMPERATURE_VIOLATION'}
    return {'status': 'VALIDATED'}

def update_inventory(state: CultureKitState):
    print(f'Syncing kit {state['kit_id']} to LIMS system')
    return {'status': 'PROCESSED'}

graph = StateGraph(CultureKitState)
graph.add_node('validate', validate_storage)
graph.add_node('inventory', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph = graph.compile()