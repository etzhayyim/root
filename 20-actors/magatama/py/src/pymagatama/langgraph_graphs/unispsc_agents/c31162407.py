from typing import TypedDict
from langgraph.graph import StateGraph, END

class LatchState(TypedDict):
    specs: dict
    validated: bool

def validate_load_capacity(state: LatchState):
    load = state['specs'].get('load_capacity', 0)
    state['validated'] = load > 0
    return state

def check_material(state: LatchState):
    allowed = ['stainless_steel', 'zinc', 'aluminum']
    state['validated'] = state['validated'] and (state['specs'].get('material') in allowed)
    return state

graph = StateGraph(LatchState)
graph.add_node("validate_load", validate_load_capacity)
graph.add_node("check_material", check_material)
graph.set_entry_point("validate_load")
graph.add_edge("validate_load", "check_material")
graph.add_edge("check_material", END)
compiled_graph = graph.compile()
