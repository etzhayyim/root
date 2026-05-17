from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BedFrameSpecs(TypedDict):
    material: str
    weight_load: int
    is_compliant: bool

def validate_specs(state: BedFrameSpecs):
    state['is_compliant'] = state['weight_load'] > 100
    return state

def assemble_part(state: BedFrameSpecs):
    print(f'Processing part with material: {state[\'material\']}')
    return state

graph = StateGraph(BedFrameSpecs)
graph.add_node('validate', validate_specs)
graph.add_node('assemble', assemble_part)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph = graph.compile()