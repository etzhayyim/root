from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GlueGunState(TypedDict):
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_specs(state: GlueGunState):
    log = []
    if state['specs'].get('wattage', 0) < 20:
        log.append('Power too low for industrial use')
    return {'validation_log': log}

def approval_check(state: GlueGunState):
    return {'approved': len(state['validation_log']) == 0}

graph = StateGraph(GlueGunState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()