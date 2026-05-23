from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MachineSpecState(TypedDict):
    cycle_speed: int
    sheet_specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_speed(state: MachineSpecState):
    errors = []
    if state['cycle_speed'] < 5000: errors.append('Speed below industry threshold')
    return {'validation_errors': errors}

def final_decision(state: MachineSpecState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(MachineSpecState)
graph.add_node('validate', validate_speed)
graph.add_node('approve', final_decision)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
