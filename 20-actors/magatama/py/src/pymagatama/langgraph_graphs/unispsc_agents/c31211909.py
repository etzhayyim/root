from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaintTrayState(TypedDict):
    tray_type: str
    solvent_resistance: bool
    approved: bool

def validate_tray_spec(state: PaintTrayState):
    if state['solvent_resistance']:
        return {'approved': True}
    return {'approved': False}

graph = StateGraph(PaintTrayState)
graph.add_node('validate', validate_tray_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()