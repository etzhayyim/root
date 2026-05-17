import operator
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class StretcherToolState(TypedDict):
    tool_spec: dict
    validation_log: Annotated[List[str], operator.add]
    is_approved: bool

def validate_tool_specs(state: StretcherToolState):
    log = []
    if state['tool_spec'].get('width', 0) <= 0:
        log.append('Invalid width detected')
    return {'validation_log': log}

def approval_check(state: StretcherToolState):
    approved = len(state['validation_log']) == 0
    return {'is_approved': approved}

graph = StateGraph(StretcherToolState)
graph.add_node('validate', validate_tool_specs)
graph.add_node('approve', approval_check)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()