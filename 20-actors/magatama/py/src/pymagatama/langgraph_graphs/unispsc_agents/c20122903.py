from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class RobotHoldingState(TypedDict):
    part_id: str
    spec_data: dict
    validation_logs: Annotated[list[str], operator.add]
    is_approved: bool

def validate_clamping_specs(state: RobotHoldingState):
    specs = state['spec_data']
    logs = []
    if specs.get('clamping_force_kn', 0) <= 0:
        logs.append('Invalid clamping force detected.')
    return {'validation_logs': logs, 'is_approved': len(logs) == 0}

def structural_integrity_check(state: RobotHoldingState):
    logs = ['Checking material hardness and load capacity...']
    return {'validation_logs': logs}

builder = StateGraph(RobotHoldingState)
builder.add_node('validate', validate_clamping_specs)
builder.add_node('integrity_check', structural_integrity_check)
builder.set_entry_point('validate')
builder.add_edge('validate', 'integrity_check')
builder.add_edge('integrity_check', END)
graph = builder.compile()
