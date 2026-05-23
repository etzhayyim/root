from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AbsorbentState(TypedDict):
    material_type: str
    absorption_capacity: float
    safety_compliance: bool
    approved: bool

def validate_absorbent(state: AbsorbentState):
    if state['absorption_capacity'] > 0 and state['safety_compliance']:
        return {'approved': True}
    return {'approved': False}

def route_by_material(state: AbsorbentState):
    if 'chemical' in state['material_type'].lower():
        return 'chemical_safety_check'
    return 'standard_check'

graph = StateGraph(AbsorbentState)
graph.add_node('chemical_safety_check', validate_absorbent)
graph.add_node('standard_check', validate_absorbent)
graph.set_entry_point('standard_check')
graph.add_edge('standard_check', END)
graph.add_edge('chemical_safety_check', END)
graph = graph.compile()
