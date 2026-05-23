from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class TitaniumPipeState(TypedDict):
    pipe_specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_material_grade(state: TitaniumPipeState):
    grade = state['pipe_specs'].get('ASTM_spec_grade')
    if not grade or 'Grade' not in grade:
        state['validation_errors'].append('Invalid or missing ASTM grade')
    return state

def check_compliance(state: TitaniumPipeState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return state

graph = StateGraph(TitaniumPipeState)
graph.add_node('validate', validate_material_grade)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
