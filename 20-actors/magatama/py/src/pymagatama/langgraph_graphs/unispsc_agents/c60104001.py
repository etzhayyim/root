from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DNAModelState(TypedDict):
    model_type: str
    is_assembled: bool
    quality_score: float

def validate_specs(state: DNAModelState):
    return {'quality_score': 1.0 if state['model_type'] == 'educational' else 0.5}

def assembly_check(state: DNAModelState):
    return {'is_assembled': True}

graph = StateGraph(DNAModelState)
graph.add_node('validate', validate_specs)
graph.add_node('assemble', assembly_check)
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
