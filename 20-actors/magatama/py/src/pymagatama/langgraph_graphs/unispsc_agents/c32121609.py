from typing import TypedDict
from langgraph.graph import StateGraph, END

class ResistorState(TypedDict):
    part_number: str
    resistance: float
    tolerance: float
    is_compliant: bool

def validate_specs(state: ResistorState):
    state['is_compliant'] = state['tolerance'] <= 5.0
    return state

def check_compliance(state: ResistorState):
    return 'compliant' if state['is_compliant'] else 'non-compliant'

graph = StateGraph(ResistorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non-compliant': END})
graph.compile()
