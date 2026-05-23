from typing import TypedDict
from langgraph.graph import StateGraph, END

class EduMaterialState(TypedDict):
    content: str
    is_curriculum_compliant: bool
    approved: bool

def validate_curriculum(state: EduMaterialState):
    compliance = 'common_core' in state['content'] or 'standard' in state['content']
    return {'is_curriculum_compliant': compliance}

def approval_check(state: EduMaterialState):
    return {'approved': state['is_curriculum_compliant']}

graph = StateGraph(EduMaterialState)
graph.add_node('validate', validate_curriculum)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
