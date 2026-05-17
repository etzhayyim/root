from typing import TypedDict
from langgraph.graph import StateGraph, END

class FondueProcurementState(TypedDict):
    material: str
    compliance_docs: bool
    capacity: float
    status: str

def validate_material(state: FondueProcurementState):
    allowed = ['stainless steel', 'cast iron', 'ceramic']
    return {'status': 'validated' if state['material'] in allowed else 'rejected'}

def check_compliance(state: FondueProcurementState):
    return {'status': 'compliant' if state['compliance_docs'] else 'pending_docs'}

graph = StateGraph(FondueProcurementState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_compliance')
graph.add_edge('check_compliance', END)

compiled_graph = graph.compile()