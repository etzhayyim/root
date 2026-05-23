from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SqueegeeState(TypedDict):
    part_number: str
    material_spec: str
    compatibility: List[str]
    approved: bool

def validate_material(state: SqueegeeState):
    state['approved'] = 'rubber' in state['material_spec'].lower() or 'silicone' in state['material_spec'].lower()
    return state

def check_compatibility(state: SqueegeeState):
    if state['approved'] and len(state['compatibility']) > 0:
        state['approved'] = True
    return state

graph = StateGraph(SqueegeeState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_compatibility', check_compatibility)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_compatibility')
graph.add_edge('check_compatibility', END)
graph = graph.compile()
