from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    curriculum_level: str
    validation_status: bool

def validate_resource(state: ProcurementState):
    state['validation_status'] = True if state['curriculum_level'] else False
    return state

def publish_order(state: ProcurementState):
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_resource)
graph.add_node('publish', publish_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'publish')
graph.add_edge('publish', END)
graph = graph.compile()
