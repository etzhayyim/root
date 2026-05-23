from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    product_name: str
    approval_status: bool
    batch_id: str
    safety_verified: bool

def validate_certification(state: DrugProcurementState):
    state['safety_verified'] = state['approval_status']
    return {'safety_verified': state['safety_verified']}

def process_batch(state: DrugProcurementState):
    print(f'Processing batch: {state['batch_id']}')
    return {'status': 'processed'}

graph = StateGraph(DrugProcurementState)
graph.add_node('validate', validate_certification)
graph.add_node('process', process_batch)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)

compiled_graph = graph.compile()
