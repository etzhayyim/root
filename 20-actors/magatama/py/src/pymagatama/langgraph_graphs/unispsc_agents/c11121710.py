from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CobaltState(TypedDict):
    purity: float
    origin: str
    is_compliant: bool
    log: Annotated[Sequence[str], operator.add]

def validate_purity(state: CobaltState) -> CobaltState:
    if state['purity'] < 99.5:
        return {'is_compliant': False, 'log': ['Purity check failed: below threshold']}
    return {'is_compliant': True, 'log': ['Purity check passed']}

def verify_origin(state: CobaltState) -> CobaltState:
    if not state['origin']:
        return {'is_compliant': False, 'log': ['Origin missing']}
    return {'is_compliant': True, 'log': ['Origin verified']}

def router(state: CobaltState) -> str:
    if not state.get('is_compliant', True):
        return 'END'
    return 'next_step'

graph = StateGraph(CobaltState)
graph.add_node('validate', validate_purity)
graph.add_node('verify', verify_origin)
graph.set_entry_point('validate')
graph.add_edge('validate', 'verify')
graph.add_edge('verify', END)
graph = graph.compile()