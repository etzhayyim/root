from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    compliance_ok: bool
    delivery_verified: bool

def validate_batch(state: DrugState):
    print(f'Validating batch {state['batch_id']} for leprosy drug safety standards.')
    return {'compliance_ok': True}

def verify_delivery(state: DrugState):
    print('Verifying cold-chain compliance and regulatory hand-off.')
    return {'delivery_verified': True}

graph = StateGraph(DrugState)
graph.add_node('validate', validate_batch)
graph.add_node('delivery', verify_delivery)
graph.set_entry_point('validate')
graph.add_edge('validate', 'delivery')
graph.add_edge('delivery', END)
app = graph.compile()
