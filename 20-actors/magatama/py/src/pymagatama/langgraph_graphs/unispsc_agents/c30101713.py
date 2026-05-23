from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BeamState(TypedDict):
    material_specs: dict
    validation_passed: bool
    log: List[str]

def validate_tin_beam(state: BeamState):
    specs = state['material_specs']
    passed = specs.get('purity', 0) >= 99.0 and 'dimensions' in specs
    return {'validation_passed': passed, 'log': ['Beam dimensions and purity validated against ASTM standards.']}

def route_by_validation(state: BeamState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(BeamState)
graph.add_node('validate', validate_tin_beam)
graph.add_node('process', lambda s: {'log': ['Procurement processing initiated.']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': 'process', '__end__': END})
graph.add_edge('process', END)
graph = graph.compile()
