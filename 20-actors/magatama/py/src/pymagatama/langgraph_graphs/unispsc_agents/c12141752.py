from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class RubberState(TypedDict):
    material_code: str
    viscosity: float
    purity_level: float
    qc_passed: bool
    validation_log: List[str]

def validate_viscosity(state: RubberState) -> RubberState:
    if 5.0 <= state['viscosity'] <= 50.0:
        state['validation_log'].append('Viscosity within operational tolerance.')
    else:
        state['validation_log'].append('Viscosity failure.')
    return state

def check_purity(state: RubberState) -> RubberState:
    if state['purity_level'] > 0.99:
        state['qc_passed'] = True
        state['validation_log'].append('Purity standards met for medical/aerospace.')
    return state

graph = StateGraph(RubberState)
graph.add_node('validate', validate_viscosity)
graph.add_node('purity', check_purity)
graph.add_edge('validate', 'purity')
graph.add_edge('purity', END)
graph.set_entry_point('validate')
graph = graph.compile()
