from typing import TypedDict
from langgraph.graph import StateGraph, END

class StationeryState(TypedDict):
    item_name: str
    quality_check: bool
    approved: bool

def validate_pen_specs(state: StationeryState):
    print(f'Validating: {state['item_name']}')
    return {'quality_check': True}

def approval_step(state: StationeryState):
    return {'approved': state['quality_check']}

graph = StateGraph(StationeryState)
graph.add_node('validate', validate_pen_specs)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)

app = graph.compile()