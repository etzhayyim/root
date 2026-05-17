from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ElectronTubeState(TypedDict):
    specs: dict
    validation_checks: List[str]
    approved: bool

def validate_specs(state: ElectronTubeState):
    checks = []
    if state['specs'].get('frequency_range'):
        checks.append('Frequency range verified')
    if state['specs'].get('vacuum_integrity_certification'):
        checks.append('Vacuum integrity valid')
    return {'validation_checks': checks, 'approved': len(checks) >= 2}

graph = StateGraph(ElectronTubeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()