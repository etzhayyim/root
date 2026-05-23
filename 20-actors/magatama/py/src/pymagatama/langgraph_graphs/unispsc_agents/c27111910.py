from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    material_hrc: int
    tip_geometry: str
    is_compliant: bool

def validate_spec(state: ToolState):
    state['is_compliant'] = state['material_hrc'] >= 60
    return state

def check_geometry(state: ToolState):
    print(f'Checking {state["tip_geometry"]} geometry')
    return state

graph = StateGraph(ToolState)
graph.add_node('validate_hardness', validate_spec)
graph.add_node('check_geometry', check_geometry)
graph.set_entry_point('validate_hardness')
graph.add_edge('validate_hardness', 'check_geometry')
graph.add_edge('check_geometry', END)

# Compilation via engine
graph = graph.compile()
