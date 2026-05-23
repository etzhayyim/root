from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    specs: dict
    validation_passed: bool
    hazard_check: bool

def validate_materials(state: AssemblyState):
    # Perform specific checks for solvent welding standards
    state['validation_passed'] = 'solvent_type' in state['specs']
    return state

def check_hazard(state: AssemblyState):
    # Identify if hazardous chemicals are involved in welding
    state['hazard_check'] = True
    return state

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_materials)
graph.add_node('hazard', check_hazard)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazard')
graph.add_edge('hazard', END)
graph = graph.compile()
