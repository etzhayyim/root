from typing import TypedDict
from langgraph.graph import StateGraph, END

class AbsorbentState(TypedDict):
    absorbent_type: str
    volume_required: float
    compatibility_check: bool
    is_compliant: bool

def validate_materials(state: AbsorbentState):
    state['compatibility_check'] = state['absorbent_type'] in ['clay', 'polymer', 'diatomaceous']
    return {'compatibility_check': state['compatibility_check']}

def check_compliance(state: AbsorbentState):
    state['is_compliant'] = state['compatibility_check'] and state['volume_required'] > 0
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(AbsorbentState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
