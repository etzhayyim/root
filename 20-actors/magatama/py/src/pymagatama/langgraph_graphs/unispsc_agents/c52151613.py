from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ScraperState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_food_safety(state: ScraperState):
    errors = []
    if state['spec_data'].get('material_grade') != 'Food-Safe':
        errors.append('Material must be food grade.')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def approval_step(state: ScraperState):
    print('Proceeding to procurement approval workflow.')
    return {'is_compliant': True}

graph = StateGraph(ScraperState)
graph.add_node('validate', validate_food_safety)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()