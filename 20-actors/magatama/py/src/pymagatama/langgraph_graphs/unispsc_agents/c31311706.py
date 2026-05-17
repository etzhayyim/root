from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeSpecState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_materials(state: PipeSpecState):
    required = ['material_type', 'pressure_rating']
    passed = all(k in state['spec_data'] for k in required)
    return {**state, 'validation_passed': passed}

def finalize_order(state: PipeSpecState):
    return {**state, 'error_log': ['Order validated successfully'] if state['validation_passed'] else ['Missing data']}

graph = StateGraph(PipeSpecState)
graph.add_node('validate', validate_materials)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()