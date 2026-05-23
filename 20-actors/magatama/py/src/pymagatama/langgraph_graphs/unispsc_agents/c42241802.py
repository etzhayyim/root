from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class OrthopedicOrderState(TypedDict):
    product_id: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_medical_cert(state: OrthopedicOrderState):
    state['validation_passed'] = 'ISO_13485' in state['compliance_docs']
    return state

def check_material_quality(state: OrthopedicOrderState):
    print(f'Checking material for {state['product_id']}')
    return state

graph = StateGraph(OrthopedicOrderState)
graph.add_node('validate_cert', validate_medical_cert)
graph.add_node('material_check', check_material_quality)
graph.set_entry_point('validate_cert')
graph.add_edge('validate_cert', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()
