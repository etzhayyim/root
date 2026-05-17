from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MaterialState(TypedDict):
    material_id: str
    purity_level: float
    particle_size: float
    status: str
    validation_log: List[str]

def validate_material(state: MaterialState) -> MaterialState:
    log = state.get('validation_log', [])
    if state['purity_level'] < 99.9:
        state['status'] = 'REJECTED'
        log.append('Purity below 99.9% threshold')
    else:
        state['status'] = 'VALIDATED'
        log.append('Purity check passed')
    state['validation_log'] = log
    return state

def route_by_status(state: MaterialState) -> str:
    return 'process_order' if state['status'] == 'VALIDATED' else 'notify_procurement'

graph = StateGraph(MaterialState)
graph.add_node('validate', validate_material)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()