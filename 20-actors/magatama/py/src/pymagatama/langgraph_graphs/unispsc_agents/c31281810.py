from typing import TypedDict
from langgraph.graph import StateGraph, END

class TitaniumState(TypedDict):
    part_specs: dict
    validation_errors: list
    compliance_cleared: bool

def validate_material(state: TitaniumState):
    grade = state['part_specs'].get('grade')
    if not grade or 'Grade' not in grade:
        state['validation_errors'].append('Invalid Material Grade specified.')
    return state

def check_compliance(state: TitaniumState):
    if not state['validation_errors']:
        state['compliance_cleared'] = True
    return state

graph = StateGraph(TitaniumState)
graph.add_node('validate_material', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'compliance')
graph.add_edge('compliance', END)

graph = graph.compile()
