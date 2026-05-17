from typing import TypedDict
from langgraph.graph import StateGraph, END

class DriveBayState(TypedDict):
    model_id: str
    compatibility_checked: bool
    dimension_validated: bool

def check_compatibility(state: DriveBayState):
    print(f'Checking compatibility for {state['model_id']}')
    return {'compatibility_checked': True}

def validate_dimensions(state: DriveBayState):
    print('Validating bay dimensions...')
    return {'dimension_validated': True}

graph = StateGraph(DriveBayState)
graph.add_node('check_comp', check_compatibility)
graph.add_node('val_dims', validate_dimensions)
graph.set_entry_point('check_comp')
graph.add_edge('check_comp', 'val_dims')
graph.add_edge('val_dims', END)
graph = graph.compile()