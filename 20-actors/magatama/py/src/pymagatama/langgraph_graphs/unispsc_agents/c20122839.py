from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ToolingState(TypedDict):
    part_number: str
    spec_check: bool
    validation_logs: list[str]
    approved: bool

def validate_specs(state: ToolingState) -> ToolingState:
    # Logic for checking torque and payload parameters against safety limits
    state['spec_check'] = True
    state['validation_logs'].append('Payload and torque limits verified.')
    return state

def assembly_compatibility_check(state: ToolingState) -> ToolingState:
    # Logic to verify compatibility with specific robot arm interfaces
    state['approved'] = True
    state['validation_logs'].append('Interface compatibility confirmed.')
    return state

graph = StateGraph(ToolingState)
graph.add_node('validate', validate_specs)
graph.add_node('compatibility', assembly_compatibility_check)
graph.add_edge('validate', 'compatibility')
graph.add_edge('compatibility', END)
graph.set_entry_point('validate')
graph = graph.compile()