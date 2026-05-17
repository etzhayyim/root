from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MiningPartsState(TypedDict):
    part_id: str
    spec_requirements: dict
    validation_results: List[str]

def validate_material(state: MiningPartsState) -> MiningPartsState:
    print(f'Validating material for {state['part_id']}')
    state['validation_results'].append('Material Grade Validated')
    return state

def check_dimensions(state: MiningPartsState) -> MiningPartsState:
    print(f'Checking dimensions for {state['part_id']}')
    state['validation_results'].append('Dimensions within Tolerance')
    return state

graph = StateGraph(MiningPartsState)
graph.add_node('material', validate_material)
graph.add_node('dimensions', check_dimensions)
graph.add_edge('material', 'dimensions')
graph.add_edge('dimensions', END)
graph.set_entry_point('material')
compiled_graph = graph.compile()