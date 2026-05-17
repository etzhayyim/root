from typing import TypedDict
from langgraph.graph import StateGraph, END

class InteriorLightState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_lighting_specs(state: InteriorLightState):
    log = []
    compliant = True
    if state['spec_data'].get('voltage', 0) not in [12, 24]:
        log.append('Invalid Voltage')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

graph = StateGraph(InteriorLightState)
graph.add_node('validator', validate_lighting_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()