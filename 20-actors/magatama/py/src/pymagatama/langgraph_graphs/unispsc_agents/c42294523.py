from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OphthalmicState(TypedDict):
    part_id: str
    is_sterile: bool
    is_regulated: bool
    approved: bool

def validate_certification(state: OphthalmicState):
    state['approved'] = state['is_sterile'] and state['is_regulated']
    return state

def check_compliance(state: OphthalmicState):
    return {'approved': True} if state['approved'] else {'approved': False}

graph = StateGraph(OphthalmicState)
graph.add_node('validate', validate_certification)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()