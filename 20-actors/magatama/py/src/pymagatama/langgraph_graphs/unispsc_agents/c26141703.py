from typing import TypedDict
from langgraph.graph import StateGraph, END
class DosimetryState(TypedDict):
    cert_file: str
    calibration_data: dict
    validated: bool
def validate_traceability(state: DosimetryState):
    print('Verifying national lab traceability certificates...')
    state['validated'] = 'NIST' in state['cert_file'] or 'NMI' in state['cert_file']
    return state
def check_uncertainty(state: DosimetryState):
    if state['calibration_data'].get('uncertainty', 1.0) > 0.05:
        raise ValueError('Uncertainty exceeds secondary standard requirements')
    return state
graph = StateGraph(DosimetryState)
graph.add_node('validate', validate_traceability)
graph.add_node('check_uncertainty', check_uncertainty)
graph.add_edge('validate', 'check_uncertainty')
graph.add_edge('check_uncertainty', END)
graph.set_entry_point('validate')
graph = graph.compile()