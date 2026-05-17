from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotState(TypedDict):
    model_id: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_robot_specs(state: RobotState):
    specs = state['specs']
    log = []
    compliant = True
    if specs.get('payload_capacity_kg', 0) <= 0:
        log.append('Invalid payload')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def export_control_check(state: RobotState):
    # Dual-use logic placeholder
    return {'validation_log': state['validation_log'] + ['Export control cleared']}

graph = StateGraph(RobotState)
graph.add_node('validate', validate_robot_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()