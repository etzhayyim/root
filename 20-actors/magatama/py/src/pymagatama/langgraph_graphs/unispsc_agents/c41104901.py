from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterSpec(TypedDict):
    pore_size: float
    material: str
    pressure_rating: float

def validate_specs(state: FilterSpec):
    if state['pore_size'] <= 0:
        return 'invalid_pore_size'
    if state['pressure_rating'] < 0:
        return 'invalid_pressure'
    return 'validated'

def process_workflow(state: FilterSpec):
    print(f'Processing filter with pore size {state['pore_size']}')
    return {'status': 'processed'}

graph = StateGraph(FilterSpec)
graph.add_node('validation', validate_specs)
graph.add_node('procurement', process_workflow)
graph.set_entry_point('validation')
graph.add_edge('validation', 'procurement')
graph.add_edge('procurement', END)
compile_graph = graph.compile()