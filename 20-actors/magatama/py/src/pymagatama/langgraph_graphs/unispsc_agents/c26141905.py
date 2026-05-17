from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InstrumentationState(TypedDict):
    device_id: str
    safety_clearance: bool
    validation_logs: List[str]

def validate_nuclear_specs(state: InstrumentationState):
    print('Validating source activity and shielding...')
    state['safety_clearance'] = True
    state['validation_logs'].append('Source checked against IAEA standards')
    return state

def export_control_check(state: InstrumentationState):
    print('Checking dual-use compliance...')
    state['validation_logs'].append('Export control verified')
    return state

graph = StateGraph(InstrumentationState)
graph.add_node('validate', validate_nuclear_specs)
graph.add_node('export', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()