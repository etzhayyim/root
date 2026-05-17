from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    assembly_id: str
    spec_data: dict
    is_validated: bool
    validation_log: List[str]

def validate_uv_weld(state: ProcessingState):
    log = []
    valid = True
    if 'UV_welding_certification' not in state['spec_data']:
        log.append('Missing UV welding certification')
        valid = False
    return {'is_validated': valid, 'validation_log': log}

def route_by_validation(state: ProcessingState):
    return 'valid' if state['is_validated'] else 'invalid'

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_uv_weld)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()