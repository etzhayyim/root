from typing import TypedDict
from langgraph.graph import StateGraph, END

class MagnesiumPipeState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_materials(state: MagnesiumPipeState):
    purity = state['specs'].get('magnesium_purity_percentage', 0)
    state['validation_passed'] = purity >= 99.0
    return {'validation_passed': state['validation_passed']}

def generate_compliance(state: MagnesiumPipeState):
    report = 'Standard ASTM check complete' if state['validation_passed'] else 'Compliance failure: Purity insufficient'
    return {'compliance_report': report}

builder = StateGraph(MagnesiumPipeState)
builder.add_node('validate', validate_materials)
builder.add_node('compliance', generate_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()
