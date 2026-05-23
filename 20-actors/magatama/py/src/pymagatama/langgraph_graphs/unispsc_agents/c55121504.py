from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KeyTagState(TypedDict):
    material: str
    specs: dict
    approved: bool

def validate_materials(state: KeyTagState):
    allowed = ['plastic', 'metal', 'acrylic']
    state['approved'] = state['material'].lower() in allowed
    return state

def finalize_order(state: KeyTagState):
    print(f'Finalizing procurement for key tags: {state.get("specs")}')
    return state

graph = StateGraph(KeyTagState)
graph.add_node('validate', validate_materials)
graph.add_node('final', finalize_order)
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph.set_entry_point('validate')
graph = graph.compile()
