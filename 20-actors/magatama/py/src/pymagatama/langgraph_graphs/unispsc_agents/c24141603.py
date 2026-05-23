from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CushioningState(TypedDict):
    material_type: str
    shock_rating: float
    compliance_checks: List[str]
    is_approved: bool

def validate_materials(state: CushioningState):
    checks = []
    if state['shock_rating'] > 0:
        checks.append('Shock Rating Validated')
    return {'compliance_checks': checks}

def approval_logic(state: CushioningState):
    is_approved = 'Shock Rating Validated' in state['compliance_checks']
    return {'is_approved': is_approved}

graph = StateGraph(CushioningState)
graph.add_node('validate', validate_materials)
graph.add_node('approve', approval_logic)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
