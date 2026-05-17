from typing import TypedDict, Annotated, List, Dict
from langgraph.graph import StateGraph, END

class RareEarthState(TypedDict):
    material_id: str
    purity: float
    origin: str
    validation_log: List[str]
    status: str

def validate_material_purity(state: RareEarthState) -> RareEarthState:
    if state['purity'] >= 99.9:
        state['validation_log'].append('High purity confirmed.')
        state['status'] = 'READY'
    else:
        state['validation_log'].append('Purity below threshold.')
        state['status'] = 'REJECTED'
    return state

def check_origin_compliance(state: RareEarthState) -> RareEarthState:
    if state['origin'] in ['Japan', 'Australia']:
        state['validation_log'].append('Origin compliant.')
    else:
        state['validation_log'].append('Review required for export compliance.')
    return state

graph = StateGraph(RareEarthState)
graph.add_node('validate', validate_material_purity)
graph.add_node('compliance', check_origin_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()