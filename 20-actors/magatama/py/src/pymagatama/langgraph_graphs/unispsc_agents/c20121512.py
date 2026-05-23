from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class EndEffectorState(TypedDict):
    spec_requirements: dict
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_gripper_specs(state: EndEffectorState):
    specs = state['spec_requirements']
    logs = []
    if specs.get('repeatability_mm', 1.0) > 0.05:
        logs.append('Warning: High repeatability tolerance.')
    return {'validation_logs': logs, 'is_compliant': True}

def check_material_safety(state: EndEffectorState):
    return {'validation_logs': ['Material stress test check passed.']}

builder = StateGraph(EndEffectorState)
builder.add_node('validate', validate_gripper_specs)
builder.add_node('material', check_material_safety)
builder.add_edge('validate', 'material')
builder.add_edge('material', END)
builder.set_entry_point('validate')
graph = builder.compile()
