from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_material(state: ForgingState):
    alloy = state['specs'].get('alloy_type')
    state['log'].append(f'Validating brass alloy: {alloy}')
    return {'validation_passed': alloy == 'C36000'}

def check_dimensions(state: ForgingState):
    state['log'].append('Checking dimensional tolerances for open die forging')
    return {'validation_passed': True}

graph = StateGraph(ForgingState)
graph.add_node('material_check', validate_material)
graph.add_node('dim_check', check_dimensions)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'dim_check')
graph.add_edge('dim_check', END)
app = graph.compile()
