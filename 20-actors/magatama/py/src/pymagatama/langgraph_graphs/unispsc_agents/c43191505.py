from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PeripheralsState(TypedDict):
    hardware_model: str
    spec_requirements: List[str]
    compliance_score: float
    validation_log: List[str]

def validate_specs(state: PeripheralsState):
    log = []
    if 'interface_compatibility' in state['spec_requirements']:
        log.append('Interface validated for standard USB-C/HID compliance.')
    return {'validation_log': log}

def assess_risk(state: PeripheralsState):
    score = 1.0 if len(state['validation_log']) > 0 else 0.5
    return {'compliance_score': score}

graph = StateGraph(PeripheralsState)
graph.add_node('validate', validate_specs)
graph.add_node('risk', assess_risk)
graph.add_edge('validate', 'risk')
graph.add_edge('risk', END)
graph.set_entry_point('validate')
graph = graph.compile()