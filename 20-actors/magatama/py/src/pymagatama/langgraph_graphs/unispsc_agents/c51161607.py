from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    purity_level: float
    has_coa: bool

def validate_compliance(state: ProcurementState):
    print(f'Validating compliance for {state['material_name']}')
    return {'is_compliant': state['has_coa'] and state['purity_level'] > 99.0}

def process_shipment(state: ProcurementState):
    print('Initiating cold chain logistics...')
    return {'status': 'processing'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_compliance)
graph.add_node('ship', process_shipment)
graph.add_edge('validate', 'ship')
graph.add_edge('ship', END)
graph.set_entry_point('validate')
graph = graph.compile()