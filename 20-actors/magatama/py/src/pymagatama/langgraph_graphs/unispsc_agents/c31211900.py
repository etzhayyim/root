from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaintToolState(TypedDict):
    tool_type: str
    material_certified: bool
    solvent_ready: bool

def validate_tool(state: PaintToolState):
    state['material_certified'] = True
    return 'validated'

def check_durability(state: PaintToolState):
    state['solvent_ready'] = True
    return 'approved'

graph = StateGraph(PaintToolState)
graph.add_node('validation', validate_tool)
graph.add_node('durability', check_durability)
graph.add_edge('validation', 'durability')
graph.add_edge('durability', END)
graph.set_entry_point('validation')
graph = graph.compile()