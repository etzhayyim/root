from langgraph.graph import StateGraph, END
from typing import TypedDict
class SprayState(TypedDict):
    pressure_psi: float
    chemical_compliance: bool
    passed_qa: bool
def validate_pressure(state: SprayState):
    state['passed_qa'] = state['pressure_psi'] > 0 and state['pressure_psi'] < 500
    return state
def authorize_usage(state: SprayState):
    if state['chemical_compliance'] and state['passed_qa']:
        return 'authorized'
    return 'flagged'
graph = StateGraph(SprayState)
graph.add_node('validate', validate_pressure)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
