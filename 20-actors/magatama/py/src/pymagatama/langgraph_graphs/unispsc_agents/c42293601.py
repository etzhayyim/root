from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BougieState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_compliance(state: BougieState):
    log = []
    compliant = True
    if 'iso13485' not in state['spec_data']: 
        compliant = False
        log.append('Missing ISO 13485 certification.')
    return {'is_compliant': compliant, 'validation_log': log}

def finalize_procurement(state: BougieState):
    return {'validation_log': state['validation_log'] + ['Procurement approved.']}

graph = StateGraph(BougieState)
graph.add_node('validate', validate_compliance)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()