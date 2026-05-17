from typing import TypedDict
from langgraph.graph import StateGraph, END

class AbrasiveState(TypedDict):
    grit: str
    rpm_limit: int
    is_compliant: bool

def validate_specs(state: AbrasiveState):
    state['is_compliant'] = state['rpm_limit'] > 0 and state['grit'] != ''
    return state

graph = StateGraph(AbrasiveState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()