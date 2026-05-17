from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CellMediaState(TypedDict):
    batch_id: str
    purity_level: float
    sterility_confirmed: bool
    log: List[str]

def validate_media(state: CellMediaState) -> CellMediaState:
    state['log'].append(f'Validating media batch {state[batch_id]}')
    state['sterility_confirmed'] = state['purity_level'] > 0.99
    return state

def archive_cert(state: CellMediaState) -> CellMediaState:
    if state['sterility_confirmed']:
        state['log'].append('Archiving certification documents')
    return state

graph = StateGraph(CellMediaState)
graph.add_node('validate', validate_media)
graph.add_node('archive', archive_cert)
graph.add_edge('validate', 'archive')
graph.add_edge('archive', END)
graph.set_entry_point('validate')
graph = graph.compile()