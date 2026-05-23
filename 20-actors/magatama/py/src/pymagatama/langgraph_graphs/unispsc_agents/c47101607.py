from typing import TypedDict
from langgraph.graph import StateGraph, END
class ChemicalState(TypedDict):
    chemical_data: dict
    validation_errors: list
    is_approved: bool
def validate_safety_compliance(state: ChemicalState):
    sds = state['chemical_data'].get('sds_present', False)
    errors = [] if sds else ['Missing SDS']
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}
def process_approval(state: ChemicalState):
    return {'is_approved': True} if not state['validation_errors'] else {'is_approved': False}
graph = StateGraph(ChemicalState)
graph.add_node('verify', validate_safety_compliance)
graph.add_node('approve', process_approval)
graph.set_entry_point('verify')
graph.add_edge('verify', 'approve')
graph.add_edge('approve', END)
graph.compile()
