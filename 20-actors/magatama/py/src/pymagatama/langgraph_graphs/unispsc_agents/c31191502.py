from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BuffState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_rpm(state: BuffState):
    if state['spec_data'].get('rpm', 0) > 10000:
        state['validation_errors'].append('RPM exceeds safety limit')
    return state

def check_material(state: BuffState):
    if not state['spec_data'].get('material'):
        state['validation_errors'].append('Material type missing')
    return state

graph = StateGraph(BuffState)
graph.add_node('rpm_check', validate_rpm)
graph.add_node('material_check', check_material)
graph.set_entry_point('rpm_check')
graph.add_edge('rpm_check', 'material_check')
graph.add_edge('material_check', END)
graph = graph.compile()
