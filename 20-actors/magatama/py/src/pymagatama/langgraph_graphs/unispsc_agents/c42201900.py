from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class XRayIlluminatorState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: XRayIlluminatorState):
    log = []
    compliant = True
    if state['specs'].get('luminance', 0) < 2000:
        log.append('Low luminance')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def process_procurement(state: XRayIlluminatorState):
    return {'validation_log': state['validation_log'] + ['Procurement workflow initiated']}

graph = StateGraph(XRayIlluminatorState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()