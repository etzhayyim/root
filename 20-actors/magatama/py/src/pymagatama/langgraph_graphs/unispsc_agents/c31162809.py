from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PinState(TypedDict):
    part_number: str
    spec_data: dict
    validated: bool

def validate_specs(state: PinState):
    # Business logic for tolerance checking
    tolerance = state['spec_data'].get('tolerance', 0.01)
    state['validated'] = tolerance <= 0.05
    return 'check_material'

def check_material(state: PinState):
    print(f'Checking material for {state.get('part_number')}')
    return 'end'

graph = StateGraph(PinState)
graph.add_node('validate', validate_specs)
graph.add_node('check_material', check_material)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_material')
graph.add_edge('check_material', END)
graph = graph.compile()