from typing import TypedDict
from langgraph.graph import StateGraph, END

class MechanicalState(TypedDict):
    part_spec: dict
    validation_passed: bool

def validate_part(state: MechanicalState):
    # Perform dimensional and metallurgical validation logic
    passed = all(['material' in state['part_spec'], 'tolerance' in state['part_spec']])
    return {'validation_passed': passed}

def route_by_validation(state: MechanicalState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(MechanicalState)
graph.add_node('validate', validate_part)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
