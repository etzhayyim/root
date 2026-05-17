from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity: float
    particle_size: float
    is_stable: bool
    validation_log: List[str]

def validate_catalyst_purity(state: CatalystState):
    log = state.get('validation_log', [])
    if state['purity'] >= 0.99:
        log.append('Purity check passed')
    else:
        log.append('Purity check failed')
    return {'validation_log': log}

def check_stability(state: CatalystState):
    log = state.get('validation_log', [])
    if state['is_stable']:
        log.append('Stability validated')
    else:
        log.append('Stability unstable')
    return {'validation_log': log}

graph = StateGraph(CatalystState)
graph.add_node('validate_purity', validate_catalyst_purity)
graph.add_node('check_stability', check_stability)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_stability')
graph.add_edge('check_stability', END)
graph = graph.compile()