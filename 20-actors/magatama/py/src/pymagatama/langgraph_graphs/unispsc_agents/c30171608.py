from langgraph.graph import StateGraph, END
from typing import TypedDict
class WindowProcurementState(TypedDict):
    specs: dict
    approved: bool
    validation_log: list
def validate_specs(state: WindowProcurementState):
    required = ['material', 'thermal_rating']
    valid = all(key in state['specs'] for key in required)
    return {'approved': valid, 'validation_log': ['Specs checked'] if valid else ['Missing specs']}
def check_compliance(state: WindowProcurementState):
    return {'validation_log': state['validation_log'] + ['Compliance verified']}
builder = StateGraph(WindowProcurementState)
builder.add_node('validate', validate_specs)
builder.add_node('compliance', check_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()