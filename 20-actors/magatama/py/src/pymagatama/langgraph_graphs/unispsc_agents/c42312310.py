from typing import TypedDict
from langgraph.graph import StateGraph, END

class WashBottleState(TypedDict):
    material: str
    capacity: int
    is_chemically_resistant: bool
    validation_status: str

def validate_material(state: WashBottleState):
    state['validation_status'] = 'Valid' if state['material'] in ['LDPE', 'PP'] else 'Invalid'
    return state

def check_chemical_compatibility(state: WashBottleState):
    if state['validation_status'] == 'Valid' and state['is_chemically_resistant']:
        state['validation_status'] = 'Approved'
    else:
        state['validation_status'] = 'Rejected'
    return state

graph = StateGraph(WashBottleState)
graph.add_node('validation', validate_material)
graph.add_node('chemical_check', check_chemical_compatibility)
graph.set_entry_point('validation')
graph.add_edge('validation', 'chemical_check')
graph.add_edge('chemical_check', END)
app = graph.compile()
