from typing import TypedDict
from langgraph.graph import StateGraph, END
class FilterSpec(TypedDict):
    pore_size: float
    material: str
    is_sterile: bool
def validate_specs(state: FilterSpec):
    if state['pore_size'] <= 0:
        raise ValueError('Pore size must be positive')
    return 'validated' if state['material'] else 'incomplete'
def compile_graph():
    graph = StateGraph(FilterSpec)
    graph.add_node('validate', validate_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()
graph = compile_graph()