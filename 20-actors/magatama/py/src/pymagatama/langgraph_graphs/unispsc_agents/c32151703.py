from typing import TypedDict
from langgraph.graph import StateGraph, END

class PLCState(TypedDict):
    spec_data: dict
    validation_log: list[str]
    is_compliant: bool

def validate_specs(state: PLCState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if 'InputVoltageRange' not in specs:
        logs.append('Missing mandatory voltage range spec')
        compliant = False
    return {'validation_log': logs, 'is_compliant': compliant}

def route_by_compliance(state: PLCState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(PLCState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
