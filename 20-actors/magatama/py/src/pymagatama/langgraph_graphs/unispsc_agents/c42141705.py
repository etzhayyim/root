from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    is_compliant: bool
    validation_log: List[str]

def validate_medical_grade(state: ProcurementState):
    log = []
    compliant = True
    if 'biocompatibility_certification' not in state['specs']:
        log.append('Missing biocompatibility certification')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': log}

def approve_procurement(state: ProcurementState): return {}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_grade)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()