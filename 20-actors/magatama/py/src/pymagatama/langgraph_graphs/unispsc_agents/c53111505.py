from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InfantFootwearState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_safety(state: InfantFootwearState):
    log = []
    compliant = True
    if state['specs'].get('chemical_safety') != 'passed':
        log.append('Chemical safety check failed.')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def route_by_compliance(state: InfantFootwearState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(InfantFootwearState)
graph.add_node('safety_check', validate_safety)
graph.add_node('process', lambda s: {'validation_log': s['validation_log'] + ['Processing order']})
graph.set_entry_point('safety_check')
graph.add_conditional_edges('safety_check', route_by_compliance)
graph.add_edge('process', END)
graph = graph.compile()
