from typing import TypedDict
from langgraph.graph import StateGraph, END

class VacuumOvenState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_specs(state: VacuumOvenState):
    # Perform check for vacuum seal integrity and safety certification
    state['validation_passed'] = 'Certification' in state['specs']
    return state

def check_compliance(state: VacuumOvenState):
    return 'compliant' if state['validation_passed'] else 'non_compliant'

graph = StateGraph(VacuumOvenState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)