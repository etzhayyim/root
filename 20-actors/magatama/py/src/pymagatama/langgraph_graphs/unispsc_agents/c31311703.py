from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    material: str
    pressure_test: bool
    ndt_passed: bool
    approved: bool

def validate_material(state: PipeState):
    state['approved'] = state['material'] == 'Hastelloy X'
    return state

def check_compliance(state: PipeState):
    if state['approved'] and state['pressure_test'] and state['ndt_passed']:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(PipeState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
