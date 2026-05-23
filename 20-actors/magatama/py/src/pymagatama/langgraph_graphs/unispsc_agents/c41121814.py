from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LabSupplyState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_spec(state: LabSupplyState):
    required = ['material_composition', 'dimensions_mm']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def quality_check(state: LabSupplyState):
    print(f'Inspecting quality for: {state["item_name"]}')
    return state

graph = StateGraph(LabSupplyState)
graph.add_node('validate', validate_spec)
graph.add_node('quality', quality_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quality')
graph.add_edge('quality', END)
graph = graph.compile()
