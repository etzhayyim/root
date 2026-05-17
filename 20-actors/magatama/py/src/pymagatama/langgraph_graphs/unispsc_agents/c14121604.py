from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class DrumProcurementState(TypedDict):
    drum_type: str
    volume: int
    un_certification: str
    inspection_passed: bool
    log: List[str]

def validate_specs(state: DrumProcurementState) -> DrumProcurementState:
    if state['volume'] > 200:
        state['log'].append('Volume exceeds standard safety threshold.')
    state['inspection_passed'] = True
    return state

def route_verification(state: DrumProcurementState) -> str:
    return 'check_hazmat'

def check_hazmat(state: DrumProcurementState) -> DrumProcurementState:
    state['log'].append('Checking UN dangerous goods compliance.')
    return state

graph = StateGraph(DrumProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('check_hazmat', check_hazmat)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_hazmat')
graph.add_edge('check_hazmat', END)
graph = graph.compile()