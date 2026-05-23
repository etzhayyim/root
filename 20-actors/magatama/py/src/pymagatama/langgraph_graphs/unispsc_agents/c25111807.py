from langgraph.graph import StateGraph, END
from typing import TypedDict
class DinghyState(TypedDict):
    specs: dict
    is_compliant: bool
def validate_specs(state: DinghyState):
    required = ['hull_material', 'safety_rating']
    valid = all(k in state['specs'] for k in required)
    return {'is_compliant': valid}
def process_approval(state: DinghyState):
    return {'is_compliant': True} if state['is_compliant'] else {'is_compliant': False}
graph = StateGraph(DinghyState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', process_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
