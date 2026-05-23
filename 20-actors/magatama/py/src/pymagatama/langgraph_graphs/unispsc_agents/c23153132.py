from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RobotEndEffectorState(TypedDict):
    part_id: str
    load_spec: dict
    validation_passed: bool
    compliance_tags: List[str]

def validate_load_capacity(state: RobotEndEffectorState):
    load = state['load_spec'].get('capacity', 0)
    return {'validation_passed': load > 0}

def check_compliance(state: RobotEndEffectorState):
    tags = []
    if state['load_spec'].get('is_dual_use', False):
        tags.append('dual-use-export-control')
    return {'compliance_tags': tags}

graph = StateGraph(RobotEndEffectorState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
