from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END

class PolysiliconState(TypedDict):
    purity: float
    dopant_level: float
    status: str
    validation_log: List[str]

def validate_purity(state: PolysiliconState) -> PolysiliconState:
    if state['purity'] >= 99.9999999:
        state['status'] = 'HIGH_GRADE'
        state['validation_log'].append('Purity validated: Electronic Grade')
    else:
        state['status'] = 'REJECTED'
        state['validation_log'].append('Purity below threshold')
    return state

def check_dopant(state: PolysiliconState) -> PolysiliconState:
    if state['status'] == 'HIGH_GRADE':
        if state['dopant_level'] < 0.001:
            state['status'] = 'APPROVED'
            state['validation_log'].append('Dopant level within specs')
        else:
            state['status'] = 'REJECTED'
            state['validation_log'].append('Dopant level exceeded')
    return state

graph = StateGraph(PolysiliconState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_dopant', check_dopant)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_dopant')
graph.add_edge('check_dopant', END)
compiled_graph = graph.compile()
