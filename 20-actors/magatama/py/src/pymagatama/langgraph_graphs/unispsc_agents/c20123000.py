from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    part_id: str
    load_profile: float
    inspection_result: bool
    history_log: List[str]

def validate_load_capacity(state: ProcessingState) -> ProcessingState:
    state['inspection_result'] = state['load_profile'] < 50000.0
    state['history_log'].append(f'Load validation: {state['inspection_result']}')
    return state

def route_by_inspection(state: ProcessingState) -> str:
    return 'process' if state['inspection_result'] else 'reject'

def process_bearing(state: ProcessingState) -> ProcessingState:
    state['history_log'].append('Bearing certified for industrial assembly')
    return state

builder = StateGraph(ProcessingState)
builder.add_node('validate', validate_load_capacity)
builder.add_node('process', process_bearing)
builder.add_edge('validate', 'process')
builder.add_conditional_edges('validate', route_by_inspection, {'process': 'process', 'reject': END})
builder.set_entry_point('validate')
builder.add_edge('process', END)
graph = builder.compile()