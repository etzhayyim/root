from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    material_grade: str
    torque_specs: dict
    is_validated: bool

def validate_specs(state: AssemblyState):
    state['is_validated'] = state['material_grade'] == '6061-T6'
    return state

def assembly_workflow(state: AssemblyState):
    return {'is_validated': state['is_validated']}

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_specs)
graph.add_node('process', assembly_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.compile()