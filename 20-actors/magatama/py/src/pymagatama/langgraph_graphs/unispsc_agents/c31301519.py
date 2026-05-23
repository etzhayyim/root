from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    spec_data: dict
    validation_result: bool
    compliance_report: str

def validate_materials(state: ForgingState):
    material = state['spec_data'].get('material_grade')
    is_valid = material is not None and len(material) > 0
    return {'validation_result': is_valid}

def generate_compliance(state: ForgingState):
    status = 'Passed' if state['validation_result'] else 'Failed'
    return {'compliance_report': f'Material compliance check: {status}'}

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
