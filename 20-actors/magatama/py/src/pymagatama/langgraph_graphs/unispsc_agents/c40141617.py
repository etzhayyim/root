from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    specs: dict
    approved: bool

def validate_pressure(state: ValveState):
    state['approved'] = state['specs'].get('psi', 0) > 0
    return state

def check_compliance(state: ValveState):
    return {'approved': state['approved'] and state['specs'].get('cert') == 'ASME'}

graph = StateGraph(ValveState)
graph.add_node('validate', validate_pressure)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
