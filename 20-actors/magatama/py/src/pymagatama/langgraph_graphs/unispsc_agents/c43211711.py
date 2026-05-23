from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ScannerState(TypedDict):
    model_number: str
    resolution_dpi: int
    encryption_compliant: bool
    validation_log: List[str]

def validate_specs(state: ScannerState):
    log = state.get('validation_log', [])
    if state['resolution_dpi'] < 600:
        log.append('Resolution below professional threshold.')
    if not state['encryption_compliant']:
        log.append('Security vulnerability: Encryption not detected.')
    return {'validation_log': log}

graph = StateGraph(ScannerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
