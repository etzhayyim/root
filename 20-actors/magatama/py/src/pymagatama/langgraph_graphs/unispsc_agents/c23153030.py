from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotControlState(TypedDict):
    device_id: str
    specs: dict
    validation_log: List[str]
    is_compliant: bool

def validate_specs(state: RobotControlState):
    log = []
    if 'IP_rating' not in state['specs']:
        log.append('Missing IP rating')
    return {'validation_log': log}

def check_compliance(state: RobotControlState):
    return {'is_compliant': len(state['validation_log']) == 0}

graph = StateGraph(RobotControlState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
