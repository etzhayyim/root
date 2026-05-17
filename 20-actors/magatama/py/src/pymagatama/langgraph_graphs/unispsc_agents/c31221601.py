from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TanningState(TypedDict):
    material_name: str
    chemical_data: dict
    approved: bool

def validate_chemical_specs(state: TanningState):
    # Business logic for verifying inorganic tanning extract quality
    specs = state['chemical_data']
    state['approved'] = specs.get('heavy_metals_ok', False) and specs.get('ph_valid', False)
    return state

def safety_check(state: TanningState):
    # Logic for hazardous material handling compliance
    print(f'Running safety compliance for {state['material_name']}')
    return {'approved': state['approved']}

graph = StateGraph(TanningState)
graph.add_node('validate', validate_chemical_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()