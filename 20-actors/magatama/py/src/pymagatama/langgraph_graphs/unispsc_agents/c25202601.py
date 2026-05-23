from typing import TypedDict
from langgraph.graph import StateGraph, END

class AircraftSpecState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_aerospace_standards(state: AircraftSpecState):
    log = []
    compliant = True
    if 'AS9100' not in state['spec_data'].get('certifications', []):
        log.append('Missing AS9100 certification')
        compliant = False
    return {'validation_log': log, 'is_compliant': compliant}

workflow = StateGraph(AircraftSpecState)
workflow.add_node('validate', validate_aerospace_standards)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
