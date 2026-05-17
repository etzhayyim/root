from typing import TypedDict
from langgraph.graph import StateGraph, END

class ElectricalTapState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: ElectricalTapState):
    log = []
    required = ['Voltage Rating', 'UL Certification']
    compliant = all(key in state['specs'] for key in required)
    if not compliant:
        log.append('Missing mandatory UL certification or electrical ratings')
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(ElectricalTapState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()