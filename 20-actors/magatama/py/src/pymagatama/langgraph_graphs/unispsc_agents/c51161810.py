from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    compliance_docs: List[str]
    is_verified: bool

def validate_pharma_specs(state: ProcurementState):
    required = ['batch_analysis', 'gmp_certificate', 'msds']
    all_present = all(doc in state['compliance_docs'] for doc in required)
    return {'is_verified': all_present}

def process_procurement(state: ProcurementState):
    return {'material_name': f'Processed {state['material_name']}'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_pharma_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
