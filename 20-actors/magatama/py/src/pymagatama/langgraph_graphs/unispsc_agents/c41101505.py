from typing import TypedDict
from langgraph.graph import StateGraph, END

class CellProcState(TypedDict):
    pressure_limit: float
    material_certified: bool
    validation_passed: bool

def validate_specs(state: CellProcState):
    passed = state['pressure_limit'] >= 60.0 and state['material_certified'] == True
    return {'validation_passed': passed}

def route_by_spec(state: CellProcState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(CellProcState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()