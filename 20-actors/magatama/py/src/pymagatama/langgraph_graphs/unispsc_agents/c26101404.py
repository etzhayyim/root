from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MotorBrushState(TypedDict):
    specifications: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: MotorBrushState):
    required = ['material_composition_carbon_ratio', 'dimensions_mm']
    errors = [f'Missing {f}' for f in required if f not in state['specifications']]
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def process_procurement(state: MotorBrushState):
    print('Processing motor brush procurement request...')
    return {'validation_passed': True}

graph = StateGraph(MotorBrushState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()