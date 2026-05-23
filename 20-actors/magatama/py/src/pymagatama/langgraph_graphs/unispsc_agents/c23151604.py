from typing import TypedDict
from langgraph.graph import StateGraph, END

class CentrifugeState(TypedDict):
    model_number: str
    rpm_rating: int
    compliance_tags: list

def validate_specs(state: CentrifugeState):
    if state['rpm_rating'] > 20000:
        state['compliance_tags'].append('export_restricted_high_speed')
    return state

def safety_check(state: CentrifugeState):
    state['compliance_tags'].append('ce_certified')
    return state

graph = StateGraph(CentrifugeState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()
