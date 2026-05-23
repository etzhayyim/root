from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EquipmentState(TypedDict):
    items: List[dict]
    status: str
    validation_errors: List[str]

def validate_ball_spec(state: EquipmentState):
    errors = []
    for item in state['items']:
        if item.get('type') == 'ball' and 'weight' not in item:
            errors.append(f'Missing weight spec for {item.get('name')}')
    return {'validation_errors': errors, 'status': 'validated' if not errors else 'failed'}

workflow = StateGraph(EquipmentState)
workflow.add_node('spec_validation', validate_ball_spec)
workflow.set_entry_point('spec_validation')
workflow.add_edge('spec_validation', END)
graph = workflow.compile()
