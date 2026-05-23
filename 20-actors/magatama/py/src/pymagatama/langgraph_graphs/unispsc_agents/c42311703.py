from typing import TypedDict
from langgraph.graph import StateGraph

class TapeState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_biocompatibility(state: TapeState) -> TapeState:
    # ISO 10993 compliance check logic
    state['is_compliant'] = 'ISO10993' in state['spec_data'].get('certs', [])
    return state

def check_adhesion(state: TapeState) -> TapeState:
    if state['spec_data'].get('adhesion', 0) < 0.5:
        state['validation_errors'].append('Insufficient adhesion strength')
    return state

graph = StateGraph(TapeState)
graph.add_node('biocompatibility', validate_biocompatibility)
graph.add_node('adhesion', check_adhesion)
graph.set_entry_point('biocompatibility')
graph.add_edge('biocompatibility', 'adhesion')
graph.set_finish_point('adhesion')
compiled_graph = graph.compile()
