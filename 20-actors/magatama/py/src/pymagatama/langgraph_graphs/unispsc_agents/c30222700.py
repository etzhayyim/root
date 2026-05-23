from typing import TypedDict
from langgraph.graph import StateGraph, END

class StructureState(TypedDict):
    specs: dict
    approved: bool

def validate_structural_specs(state: StructureState):
    required = ['grade', 'load_capacity', 'seismic_cert']
    all_present = all(k in state['specs'] for k in required)
    return {'approved': all_present}

graph = StateGraph(StructureState)
graph.add_node('validate', validate_structural_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
