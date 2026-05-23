from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class MineralProcessState(TypedDict):
    material_code: str
    purity_level: float
    certification_passed: bool
    validation_log: List[str]

def validate_material(state: MineralProcessState) -> MineralProcessState:
    if state.get('purity_level', 0) >= 99.9:
        state['certification_passed'] = True
        state['validation_log'].append('High purity confirmed.')
    else:
        state['certification_passed'] = False
        state['validation_log'].append('Purity below threshold.')
    return state

def check_compliance(state: MineralProcessState) -> MineralProcessState:
    if state['certification_passed']:
        state['validation_log'].append('Compliance checked and passed.')
    return state

graph = StateGraph(MineralProcessState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
compile = graph.compile()
