from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RobotProcessState(TypedDict):
    model_id: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: RobotProcessState):
    log = []
    if state['specs'].get('payload_capacity_kg', 0) > 1000:
        log.append('High payload detected: trigger safety compliance')
    return {'is_compliant': True, 'validation_log': log}

def export_control_check(state: RobotProcessState):
    # Simulate dual-use export check
    return {'validation_log': state['validation_log'] + ['Export compliance confirmed']}

graph = StateGraph(RobotProcessState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
process_graph = graph.compile()
