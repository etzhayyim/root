from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CraftPaperState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_adhesive_specs(state: CraftPaperState):
    errors = []
    if state['spec_data'].get('adhesive_type') not in ['permanent', 'repositionable']:
        errors.append('Invalid adhesive type')
    return {'validation_errors': errors}

def approve_procurement(state: CraftPaperState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(CraftPaperState)
graph.add_node('validate', validate_adhesive_specs)
graph.add_node('approve', approve_procurement)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
