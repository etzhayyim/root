from typing import TypedDict
from langgraph.graph import StateGraph, END
class BusinessCaseState(TypedDict):
    material: str
    lock_type: str
    is_compliant: bool

def validate_specs(state: BusinessCaseState):
    compliant = state['material'] in ['Leather', 'Ballistic Nylon'] and state['lock_type'] != 'None'
    return {'is_compliant': compliant}

graph = StateGraph(BusinessCaseState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()