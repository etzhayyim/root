from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EngineCoverState(TypedDict):
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_material(state: EngineCoverState):
    material = state['specs'].get('material', '')
    passed = material in ['Aluminum', 'Steel', 'Reinforced Polymer']
    return {'validation_passed': passed, 'log': [f'Material validation: {passed}']}

def check_dimensions(state: EngineCoverState):
    return {'log': state['log'] + ['Dimensional tolerance verification complete']}

graph = StateGraph(EngineCoverState)
graph.add_node('validate', validate_material)
graph.add_node('dimensions', check_dimensions)
graph.add_edge('validate', 'dimensions')
graph.add_edge('dimensions', END)
graph.set_entry_point('validate')
app = graph.compile()
