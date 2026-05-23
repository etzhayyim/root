from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    assembly_id: str
    material_grade: str
    weld_quality_check: bool
    approved: bool

def validate_spec(state: AssemblyState) -> AssemblyState:
    if state['material_grade'] in ['304', '316L'] and state['weld_quality_check']:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph_builder = StateGraph(AssemblyState)
graph_builder.add_node('validate_spec', validate_spec)
graph_builder.set_entry_point('validate_spec')
graph_builder.add_edge('validate_spec', END)
graph = graph_builder.compile()
