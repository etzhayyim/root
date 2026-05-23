from typing import TypedDict
from langgraph.graph import StateGraph, END

class WeldingGraphState(TypedDict):
    spec_data: dict
    is_compliant: bool
    error_log: list

def validate_laser_safety(state: WeldingGraphState):
    laser_class = state['spec_data'].get('Laser Class')
    is_safe = laser_class in ['Class 1', 'Class 4']
    return {'is_compliant': is_safe, 'error_log': [] if is_safe else ['Invalid Laser Class']}

def check_dual_use(state: WeldingGraphState):
    # Simulate dual-use regulatory check
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(WeldingGraphState)
graph.add_node('safety_check', validate_laser_safety)
graph.add_node('export_check', check_dual_use)
graph.add_edge('safety_check', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('safety_check')
