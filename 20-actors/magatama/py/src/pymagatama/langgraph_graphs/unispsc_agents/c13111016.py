from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AluminumProcessState(TypedDict):
    material_code: str
    purity: float
    alloy_type: str
    inspection_passed: bool
    validation_log: List[str]

def validate_material(state: AluminumProcessState) -> AluminumProcessState:
    log = state.get('validation_log', [])
    if state['purity'] >= 99.0:
        log.append(f'Purity {state["purity"]} acceptable for alloy {state["alloy_type"]}')
        state['inspection_passed'] = True
    else:
        log.append('Purity below industry threshold')
        state['inspection_passed'] = False
    state['validation_log'] = log
    return state

def route_by_inspection(state: AluminumProcessState) -> str:
    return 'check' if state['inspection_passed'] else END

def stage_material(state: AluminumProcessState) -> AluminumProcessState:
    state['validation_log'].append('Material staged for production')
    return state

graph = StateGraph(AluminumProcessState)
graph.add_node('validate', validate_material)
graph.add_node('stage', stage_material)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_inspection, {'check': 'stage'})
graph.add_edge('stage', END)
graph = graph.compile()