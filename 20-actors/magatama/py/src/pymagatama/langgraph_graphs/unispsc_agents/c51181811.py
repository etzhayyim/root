from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    batch_id: str
    purity_level: float
    compliance_docs: List[str]
    validation_status: str

def validate_gmp(state: PharmaState):
    # Simulate strict GMP compliance check logic
    is_compliant = 'GMP_CERT' in state['compliance_docs'] and state['purity_level'] > 99.5
    return {'validation_status': 'APPROVED' if is_compliant else 'REJECTED'}

def process_shipment(state: PharmaState):
    print(f'Processing batch {state['batch_id']} for pharmaceutical distribution.')
    return {'validation_status': 'SHIPPED'}

graph = StateGraph(PharmaState)
graph.add_node('validate_gmp', validate_gmp)
graph.add_node('process', process_shipment)
graph.set_entry_point('validate_gmp')
graph.add_edge('validate_gmp', 'process')
graph.add_edge('process', END)
graph = graph.compile()