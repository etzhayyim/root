from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnaceState(TypedDict):
    temp_rating: int
    material_spec: str
    approved: bool

def validate_specs(state: FurnaceState):
    is_valid = state['temp_rating'] >= 1200 and state['material_spec'] == 'Alumina'
    return {'approved': is_valid}

def process_procurement(state: FurnaceState):
    print(f'Processing plate with rating: {state['temp_rating']}')
    return state

graph = StateGraph(FurnaceState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
app = graph.compile()