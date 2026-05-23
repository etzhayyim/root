from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class GPUProcState(TypedDict):
    gpu_id: str
    spec_requirements: dict
    validation_score: float

def validate_gpu_specs(state: GPUProcState) -> GPUProcState:
    # Logic to validate industrial GPU specs
    state['validation_score'] = 1.0 if 'thermal_design_power' in state['spec_requirements'] else 0.0
    return state

def optimize_configuration(state: GPUProcState) -> GPUProcState:
    # Logic to optimize power/performance for the specific application
    return state

builder = StateGraph(GPUProcState)
builder.add_node('validate', validate_gpu_specs)
builder.add_node('optimize', optimize_configuration)
builder.add_edge('validate', 'optimize')
builder.add_edge('optimize', END)
builder.set_entry_point('validate')
graph = builder.compile()
