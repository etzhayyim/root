from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToyProcurementState(TypedDict):
    item_name: str
    safety_verified: bool
    compliance_docs: list

def validate_safety(state: ToyProcurementState):
    print(f'Validating safety standards for {state['item_name']}')
    return {'safety_verified': True}

def process_procurement(state: ToyProcurementState):
    print('Procurement processing complete.')
    return {}

graph = StateGraph(ToyProcurementState)
graph.add_node('validate', validate_safety)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
