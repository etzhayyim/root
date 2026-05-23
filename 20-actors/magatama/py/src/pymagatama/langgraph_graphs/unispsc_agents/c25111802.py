from typing import TypedDict
from langgraph.graph import StateGraph, END

class BoatState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_hull(state: BoatState):
    passed = state['specs'].get('hull_material') in ['Fiberglass', 'Aluminum']
    return {'validation_passed': passed}

def check_safety(state: BoatState):
    return {'validation_passed': state['validation_passed'] and state['specs'].get('safety_certified')}

graph = StateGraph(BoatState)
graph.add_node('validate_hull', validate_hull)
graph.add_node('check_safety', check_safety)
graph.add_edge('validate_hull', 'check_safety')
graph.add_edge('check_safety', END)
graph.set_entry_point('validate_hull')
graph = graph.compile()
