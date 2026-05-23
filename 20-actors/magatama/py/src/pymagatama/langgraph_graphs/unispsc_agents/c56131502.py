from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeadFormState(TypedDict):
    material: str
    circumference: float
    qc_passed: bool

def validate_specs(state: HeadFormState):
    state['qc_passed'] = state['circumference'] >= 50.0 and state['circumference'] <= 65.0
    return state

def check_material(state: HeadFormState):
    if state['material'] not in ['fiberglass', 'plastic', 'styrofoam']:
        raise ValueError('Invalid material specified')
    return state

graph = StateGraph(HeadFormState)
graph.add_node('validate', validate_specs)
graph.add_node('check_material', check_material)
graph.add_edge('check_material', 'validate')
graph.add_edge('validate', END)
graph.set_entry_point('check_material')

app = graph.compile()
