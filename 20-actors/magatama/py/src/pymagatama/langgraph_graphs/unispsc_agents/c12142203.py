from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class WaferState(TypedDict):
    spec_id: str
    crystal_orientation: str
    resistivity: float
    inspection_result: bool
    validation_log: List[str]

def validate_crystal(state: WaferState) -> WaferState:
    if state['crystal_orientation'] not in ['100', '111']:
        state['validation_log'].append('Invalid orientation')
        state['inspection_result'] = False
    return state

def check_resistivity(state: WaferState) -> WaferState:
    if 1.0 <= state['resistivity'] <= 100.0:
        state['validation_log'].append('Resistivity in range')
    else:
        state['inspection_result'] = False
        state['validation_log'].append('Resistivity out of range')
    return state

graph = StateGraph(WaferState)
graph.add_node('validate_crystal', validate_crystal)
graph.add_node('check_resistivity', check_resistivity)
graph.set_entry_point('validate_crystal')
graph.add_edge('validate_crystal', 'check_resistivity')
graph.add_edge('check_resistivity', END)
graph = graph.compile()
