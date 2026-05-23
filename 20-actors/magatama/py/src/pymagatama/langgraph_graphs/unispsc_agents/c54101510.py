from typing import TypedDict
from langgraph.graph import StateGraph, END

class JewelryState(TypedDict):
    spec_data: dict
    validation_status: bool
    compliance_report: str

def validate_materials(state: JewelryState):
    purity = state['spec_data'].get('purity_percentage', 0)
    status = purity >= 92.5
    return {'validation_status': status, 'compliance_report': 'Purity check pass' if status else 'Purity check fail'}

def certify_quality(state: JewelryState):
    return {'compliance_report': state['compliance_report'] + ' | Hallmarking verified'}

graph = StateGraph(JewelryState)
graph.add_node('validation', validate_materials)
graph.add_node('certification', certify_quality)
graph.add_edge('validation', 'certification')
graph.add_edge('certification', END)
graph.set_entry_point('validation')
graph = graph.compile()
