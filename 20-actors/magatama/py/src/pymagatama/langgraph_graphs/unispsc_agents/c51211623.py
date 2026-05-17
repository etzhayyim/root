from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    product_id: str
    quality_docs: list
    is_compliant: bool

def validate_pharma_docs(state: ProcurementState):
    # Perform specific checks for pharmaceutical certifications
    state['is_compliant'] = 'CoA' in state['quality_docs'] and 'GMP' in state['quality_docs']
    return state

def check_storage_requirements(state: ProcurementState):
    # Simulate logistics validation
    print(f'Validating specialized storage for {state['product_id']}')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_docs', validate_pharma_docs)
graph.add_node('check_storage', check_storage_requirements)
graph.add_edge('validate_docs', 'check_storage')
graph.add_edge('check_storage', END)
graph.set_entry_point('validate_docs')
graph = graph.compile()