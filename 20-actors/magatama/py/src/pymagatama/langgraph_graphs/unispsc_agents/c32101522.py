from typing import TypedDict
from langgraph.graph import StateGraph, END

class IsolationState(TypedDict):
    spec_data: dict
    validation_status: str

def validate_specs(state: IsolationState):
    specs = state['spec_data']
    if 'isolation_voltage_kv' in specs and specs['isolation_voltage_kv'] > 0:
        return {'validation_status': 'APPROVED'}
    return {'validation_status': 'REJECTED'}

def export_check(state: IsolationState):
    # Dual-use compliance logic placeholder
    return {'validation_status': 'COMPLIANT'}

graph = StateGraph(IsolationState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_check)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()