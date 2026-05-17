from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class FolderState(TypedDict):
    folder_id: str
    spec: dict
    validation_log: List[str]
    is_compliant: bool

def validate_spec(state: FolderState) -> FolderState:
    spec = state['spec']
    logs = []
    if spec.get('paper_weight_gsm', 0) < 150:
        logs.append('Insufficient paper weight for standard folders.')
    state['validation_log'] = logs
    state['is_compliant'] = len(logs) == 0
    return state

def check_dimensions(state: FolderState) -> FolderState:
    if not state.get('is_compliant', False):
        return state
    dims = state['spec'].get('dimensions_mm', {})
    if dims.get('width', 0) < 220 or dims.get('height', 0) < 300:
        state['validation_log'].append('Dimensions below standard A4/Letter size.')
        state['is_compliant'] = False
    return state

builder = StateGraph(FolderState)
builder.add_node('validate', validate_spec)
builder.add_node('check_dims', check_dimensions)
builder.add_edge('validate', 'check_dims')
builder.add_edge('check_dims', END)
builder.set_entry_point('validate')
graph = builder.compile()