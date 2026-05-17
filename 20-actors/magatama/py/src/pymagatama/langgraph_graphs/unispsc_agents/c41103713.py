from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ViscosityState(TypedDict):
    temp_range: float
    iso_certified: bool
    validation_logs: List[str]

def validate_bath_specs(state: ViscosityState):
    logs = []
    if state['temp_range'] < 0:
        logs.append('Error: Temperature range must be positive')
    if not state.get('iso_certified', False):
        logs.append('Warning: Missing ISO certification verification')
    return {'validation_logs': logs}

def finalize_procurement(state: ViscosityState):
    status = 'APPROVED' if not state['validation_logs'] else 'REJECTED'
    return {'validation_logs': state['validation_logs'] + [f'Final status: {status}']}

graph = StateGraph(ViscosityState)
graph.add_node('validate', validate_bath_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()