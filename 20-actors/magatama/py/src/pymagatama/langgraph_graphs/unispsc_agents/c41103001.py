from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CoolingProbeState(TypedDict):
    probe_id: str
    spec_data: dict
    validation_logs: List[str]
    is_compliant: bool

def validate_specs(state: CoolingProbeState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if 'temperature_range_celsius' not in specs:
        logs.append('Missing temperature specifications')
        compliant = False
    return {**state, 'validation_logs': logs, 'is_compliant': compliant}

def update_compliance(state: CoolingProbeState):
    return {**state}

graph = StateGraph(CoolingProbeState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', update_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()