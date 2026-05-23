from typing import TypedDict
from langgraph.graph import StateGraph, END

class VentilatorComponentState(TypedDict):
    spec_sheet: dict
    is_compliant: bool
    validation_log: list[str]

def validate_medical_grade(state: VentilatorComponentState):
    log = []
    compliant = True
    if 'ISO_10993' not in state['spec_sheet'].get('certs', []):
        log.append('Missing ISO 10993 certification')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(VentilatorComponentState)
graph.add_node('validate', validate_medical_grade)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
