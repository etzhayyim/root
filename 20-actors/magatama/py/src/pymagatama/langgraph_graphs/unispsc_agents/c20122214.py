from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class DriveState(TypedDict):
    part_number: str
    torque_capacity: float
    specs_verified: bool
    compliance_tags: Annotated[list[str], operator.add]

def validate_specs(state: DriveState):
    verified = state['torque_capacity'] > 0
    return {'specs_verified': verified}

def check_compliance(state: DriveState):
    tags = []
    if state['torque_capacity'] > 100:
        tags.append('high-torque-export-review')
    return {'compliance_tags': tags}

graph = StateGraph(DriveState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()