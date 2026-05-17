from typing import TypedDict
from langgraph.graph import StateGraph, END

class LiftSpecification(TypedDict):
    swl: int
    is_certified: bool
    validation_status: str

def validate_specs(state: LiftSpecification):
    if state['swl'] > 0 and state['is_certified']:
        state['validation_status'] = 'COMPLIANT'
    else:
        state['validation_status'] = 'REJECTED'
    return state

graph = StateGraph(LiftSpecification)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()