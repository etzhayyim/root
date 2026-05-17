from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpecimenState(TypedDict):
    specimen_type: str
    integrity_check: bool
    compliance_cleared: bool

def validate_specimen(state: SpecimenState):
    state['integrity_check'] = True
    return 'check_compliance'

def check_compliance(state: SpecimenState):
    state['compliance_cleared'] = True if state.get('specimen_type') != 'restricted' else False
    return END

graph = StateGraph(SpecimenState)
graph.add_node('validate', validate_specimen)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate', 'check_compliance')
graph.set_entry_point('validate')
graph.compile()