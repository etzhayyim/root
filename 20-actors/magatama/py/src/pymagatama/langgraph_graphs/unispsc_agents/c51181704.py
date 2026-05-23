from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugProcurementState(TypedDict):
    drug_name: str
    purity_level: float
    compliance_docs: list
    shipping_temp: dict

def validate_purity(state: DrugProcurementState):
    assert state['purity_level'] >= 99.0, 'Purity below threshold'
    return {'status': 'validated'}

def check_compliance(state: DrugProcurementState):
    if 'GMP' not in state['compliance_docs']:
        raise ValueError('Missing GMP certification')
    return {'status': 'compliant'}

graph_builder = StateGraph(DrugProcurementState)
graph_builder.add_node('validate', validate_purity)
graph_builder.add_node('compliance', check_compliance)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'compliance')
graph_builder.add_edge('compliance', END)
graph = graph_builder.compile()
