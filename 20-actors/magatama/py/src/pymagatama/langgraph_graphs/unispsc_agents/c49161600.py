from langgraph.graph import StateGraph, END
from typing import TypedDict

class EquipmentState(TypedDict):
    item_name: str
    specs: dict
    approved: bool

def validate_specs(state: EquipmentState):
    # Business logic for sport equipment standards
    state['approved'] = all(k in state['specs'] for k in ['weight', 'material', 'safety_cert'])
    print(f'Validation complete: {state['approved']}')
    return state

graph = StateGraph(EquipmentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()