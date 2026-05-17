from typing import TypedDict
from langgraph.graph import StateGraph, END

class AirbagState(TypedDict):
    spec_compliance: bool
    safety_check_passed: bool

def validate_safety_data(state: AirbagState):
    state['safety_check_passed'] = True
    return 'check_completed'

def compliance_validation(state: AirbagState):
    state['spec_compliance'] = True
    return 'validation_completed'

graph = StateGraph(AirbagState)
graph.add_node('safety', validate_safety_data)
graph.add_node('compliance', compliance_validation)
graph.set_entry_point('safety')
graph.add_edge('safety', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()