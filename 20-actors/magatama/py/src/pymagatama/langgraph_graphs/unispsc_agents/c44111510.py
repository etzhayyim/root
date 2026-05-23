from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OrganizerState(TypedDict):
    item_id: str
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_load_capacity(state: OrganizerState):
    capacity = state['specs'].get('load_capacity', 0)
    if capacity > 0:
        return {'validation_log': state['validation_log'] + ['Capacity verified']}
    return {'validation_log': state['validation_log'] + ['Capacity failed']}

def check_compliance(state: OrganizerState):
    return {'approved': True}

graph = StateGraph(OrganizerState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
