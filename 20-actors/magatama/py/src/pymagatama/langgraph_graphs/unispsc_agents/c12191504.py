from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AdhesiveState(TypedDict):
    composition: str
    viscosity: float
    is_compliant: bool
    log: List[str]

def validate_material(state: AdhesiveState):
    is_valid = state['viscosity'] > 0 and 'composition' in state
    return {'is_compliant': is_valid, 'log': state.get('log', []) + ['Validation complete']}

def process_curing(state: AdhesiveState):
    if state['is_compliant']:
        return {'log': state.get('log', []) + ['Curing protocol initiated']}
    return {'log': state.get('log', []) + ['Curing aborted: non-compliant']}

graph = StateGraph(AdhesiveState)
graph.add_node('validate', validate_material)
graph.add_node('cure', process_curing)
graph.add_edge('validate', 'cure')
graph.add_edge('cure', END)
graph.set_entry_point('validate')
graph = graph.compile()
