from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrillState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: DrillState):
    required = ['motor_power_rating', 'drilling_capacity_mm']
    logs = [key for key in required if key not in state['specs']]
    return {'is_compliant': len(logs) == 0, 'validation_log': logs}

def safety_check(state: DrillState):
    if state.get('is_compliant'):
        return 'final'
    return 'review'

graph = StateGraph(DrillState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()