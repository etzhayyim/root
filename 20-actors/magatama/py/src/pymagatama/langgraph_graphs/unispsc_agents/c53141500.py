from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    approved: bool
    validation_log: List[str]

def validate_durability(state: ProcurementState):
    log = state.get('validation_log', [])
    if state['specs'].get('tensile_strength', 0) > 50:
        log.append('Durability validated.')
    else:
        log.append('Durability insufficient.')
    return {'validation_log': log}

def check_compliance(state: ProcurementState):
    log = state.get('validation_log', [])
    log.append('Compliance check complete.')
    return {'validation_log': log, 'approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_durability)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
