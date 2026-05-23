from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MerchGraphState(TypedDict):
    material_id: str
    curriculum_level: str
    validation_passed: bool
    errors: List[str]

def validate_curriculum(state: MerchGraphState):
    errors = []
    if not state.get('curriculum_level'):
        errors.append('Missing curriculum level designation')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def update_inventory(state: MerchGraphState):
    print(f'Syncing educational material {state['material_id']} to catalog')
    return {'validation_passed': True}

graph = StateGraph(MerchGraphState)
graph.add_node('validate', validate_curriculum)
graph.add_node('catalog', update_inventory)
graph.add_edge('validate', 'catalog')
graph.add_edge('catalog', END)
graph.set_entry_point('validate')
graph = graph.compile()
