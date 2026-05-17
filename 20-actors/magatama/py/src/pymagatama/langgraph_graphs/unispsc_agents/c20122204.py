from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class BearingState(TypedDict):
    specs: dict
    validation_log: Annotated[List[str], add_messages]
    is_approved: bool

def validate_specs(state: BearingState):
    log = []
    if state['specs'].get('load_capacity') < 1000:
        log.append('Load capacity too low for industrial grade')
    return {'validation_log': log}

def determine_approval(state: BearingState):
    is_approved = len(state['validation_log']) == 0
    return {'is_approved': is_approved}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', determine_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()