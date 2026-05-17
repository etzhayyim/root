from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    specs: dict
    validated: bool

def validate_medical_grade(state: ProcurementState):
    is_valid = 'antimicrobial' in state['specs'].get('certifications', [])
    return {'validated': is_valid}

def process_recliner_order(state: ProcurementState):
    return {'status': 'processed'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_medical_grade)
graph.add_node('process', process_recliner_order)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()