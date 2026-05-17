from typing import TypedDict
from langgraph.graph import StateGraph, END

class MedicalSpecState(TypedDict):
    product_id: str
    compliance_docs: list
    is_cleared: bool

def check_compliance(state: MedicalSpecState):
    state['is_cleared'] = all(['ISO_13485' in doc for doc in state['compliance_docs']])
    return state

def process_shipment(state: MedicalSpecState):
    print(f'Processing shipment for {state.get('product_id')}')
    return state

graph = StateGraph(MedicalSpecState)
graph.add_node('compliance', check_compliance)
graph.add_node('shipment', process_shipment)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'shipment')
graph.add_edge('shipment', END)
app = graph.compile()