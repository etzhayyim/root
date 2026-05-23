from typing import TypedDict
from langgraph.graph import StateGraph, END

class EffectState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: EffectState):
    required = ['safety_certification_ce_ul', 'dmx_compatibility']
    compliance = all(k in state['specs'] for k in required)
    return {'is_compliant': compliance}

graph = StateGraph(EffectState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
