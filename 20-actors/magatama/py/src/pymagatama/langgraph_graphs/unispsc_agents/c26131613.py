from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DuctJointState(TypedDict):
    material_specs: dict
    compliance_check: bool
    thermal_rating: float

def validate_thermal_spec(state: DuctJointState):
    state['compliance_check'] = state['thermal_rating'] >= 400.0
    return state

def check_material_integrity(state: DuctJointState):
    print('Verifying material stress resistance...')
    return state

graph = StateGraph(DuctJointState)
graph.add_node('validate', validate_thermal_spec)
graph.add_node('integrity', check_material_integrity)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integrity')
graph.add_edge('integrity', END)
app = graph.compile()