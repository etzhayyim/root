from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EngineState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: EngineState):
    specs = state['specs']
    log = []
    compliant = True
    if specs.get('rpm_range', 0) <= 0:
        log.append('Invalid RPM range')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def route_by_compliance(state: EngineState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(EngineState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: {'validation_log': x['validation_log'] + ['Processing engine order']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph = graph.compile()
