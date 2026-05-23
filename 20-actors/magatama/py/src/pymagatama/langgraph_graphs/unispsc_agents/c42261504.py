import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class AutopsyToolState(TypedDict):
    spec_data: dict
    validation_errors: Annotated[list, operator.add]
    is_approved: bool

def validate_materials(state: AutopsyToolState):
    # Validate that materials are medical grade stainless steel
    if state['spec_data'].get('material') != 'medical_grade_steel':
        return {'validation_errors': ['Invalid material class']}
    return {'validation_errors': []}

def check_compliance(state: AutopsyToolState):
    errors = state.get('validation_errors', [])
    return {'is_approved': len(errors) == 0}

graph = StateGraph(AutopsyToolState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()
