from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class LivestockState(TypedDict):
    product_id: str
    inspection_passed: bool
    compliance_tags: List[str]

def validate_health_cert(state: LivestockState) -> LivestockState:
    # Logic to verify health certification document
    state['inspection_passed'] = True
    state['compliance_tags'].append('certified_safe')
    return state

def log_inventory(state: LivestockState) -> LivestockState:
    # Logic to record in supply chain system
    print(f'Inventory logged for {state["product_id"]}')
    return state

graph = StateGraph(LivestockState)
graph.add_node('validate', validate_health_cert)
graph.add_node('log', log_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'log')
graph.add_edge('log', END)

# Compile the graph
app = graph.compile()
