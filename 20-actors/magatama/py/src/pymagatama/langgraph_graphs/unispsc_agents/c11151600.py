from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    material_id: str
    purity_level: float
    inspection_passed: bool
    log: List[str]

def validate_purity(state: MineralState) -> MineralState:
    if state['purity_level'] >= 99.0:
        state['inspection_passed'] = True
        state['log'].append('Purity check passed: >99%')
    else:
        state['inspection_passed'] = False
        state['log'].append('Purity check failed')
    return state

def process_material(state: MineralState) -> MineralState:
    if state['inspection_passed']:
        state['log'].append('Processing chemical refinement steps')
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_material)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
