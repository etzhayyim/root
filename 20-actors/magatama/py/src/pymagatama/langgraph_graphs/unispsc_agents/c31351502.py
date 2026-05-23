from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    specs: dict
    validated: bool
    errors: List[str]

def validate_specs(state: AssemblyState):
    required = ['material_grade', 'pressure_rating']
    missing = [f for f in required if f not in state['specs']]
    return {'validated': len(missing) == 0, 'errors': missing}

def build_graph():
    graph = StateGraph(AssemblyState)
    graph.add_node('validate', validate_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = build_graph()
