from typing import TypedDict
from langgraph.graph import StateGraph, END

class TankSpecState(TypedDict):
    tank_id: str
    material: str
    pressure_test_passed: bool
    is_compliant: bool

def validate_materials(state: TankSpecState):
    allowed = ['stainless_steel', 'hdpe', 'fiberglass']
    return {'is_compliant': state['material'] in allowed}

def final_check(state: TankSpecState):
    return {'is_compliant': state.get('pressure_test_passed', False) and state.get('is_compliant', False)}

graph = StateGraph(TankSpecState)
graph.add_node('validate', validate_materials)
graph.add_node('final', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()