from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeadlightState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list[str]

def validate_specs(state: HeadlightState):
    log = []
    compliant = True
    if state['specs'].get('ip_rating', 0) < 67:
        log.append('IP rating insufficient for automotive outdoor use.')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(HeadlightState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile = graph.compile()
