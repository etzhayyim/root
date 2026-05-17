from langgraph.graph import StateGraph, END
from typing import TypedDict
class WrenchState(TypedDict):
    material_grade: str
    jaw_capacity: float
    compliance_ok: bool

def validate_specs(state: WrenchState):
    state['compliance_ok'] = state['material_grade'] in ['Cr-V', 'Cr-Mo'] and state['jaw_capacity'] > 0
    return state

graph = StateGraph(WrenchState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()