from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    approved: bool

def validate_medical_standards(state: ProcurementState):
    # Simulate regulatory validation logic
    state['approved'] = 'ISO_13485' in state['compliance_docs']
    return state

def process_procurement(state: ProcurementState):
    print(f'Processing medical device purchase for: {state['product_id']}')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_standards)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()