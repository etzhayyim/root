from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PumpState(TypedDict):
    flow_rate: float
    iso_certified: bool
    validation_logs: List[str]

def validate_pump_spec(state: PumpState):
    logs = state.get('validation_logs', [])
    if state['flow_rate'] > 0:
        logs.append('Flow rate validated.')
    return {'validation_logs': logs}

def check_compliance(state: PumpState):
    logs = state.get('validation_logs', [])
    if state['iso_certified']:
        logs.append('Compliance confirmed.')
    return {'validation_logs': logs}

graph = StateGraph(PumpState)
graph.add_node('validate', validate_pump_spec)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
