from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class JerrycanState(TypedDict):
    capacity: float
    material: str
    is_un_certified: bool
    validation_passed: bool
def validate_specs(state: JerrycanState):
    state['validation_passed'] = state['capacity'] > 0 and state['is_un_certified'] == True
    return state
def check_compliance(state: JerrycanState):
    return 'compliant' if state['validation_passed'] else 'non-compliant'
graph = StateGraph(JerrycanState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
