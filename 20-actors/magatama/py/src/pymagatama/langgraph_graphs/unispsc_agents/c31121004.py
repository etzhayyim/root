from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    specs: dict
    validation_log: List[str]
    is_approved: bool

def validate_material(state: CastingState):
    grade = state['specs'].get('grade')
    if grade in ['SUS304', 'SUS316', 'SUS316L']:
        state['validation_log'].append('Material grade validated.')
    else:
        state['validation_log'].append('Invalid material grade.')
    return state

def check_compliance(state: CastingState):
    compliance = state['specs'].get('compliance_docs', False)
    state['is_approved'] = compliance
    return state

graph = StateGraph(CastingState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
