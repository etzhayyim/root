from typing import TypedDict
from langgraph.graph import StateGraph, END

class LanyardState(TypedDict):
    material: str
    breakaway_safety: bool
    compliance_checked: bool

def validate_materials(state: LanyardState):
    print(f'Checking material safety: {state["material"]}')
    return {'compliance_checked': True}

graph = StateGraph(LanyardState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()