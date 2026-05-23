from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CoreState(TypedDict):
    specifications: dict
    validation_passed: bool
    security_clearance: bool

def validate_material(state: CoreState):
    purity = state['specifications'].get('purity_percentage', 0)
    return {'validation_passed': purity >= 99.9}

def security_check(state: CoreState):
    return {'security_clearance': True}

graph = StateGraph(CoreState)
graph.add_node('validate', validate_material)
graph.add_node('security', security_check)
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph.set_entry_point('validate')
graph = graph.compile()
