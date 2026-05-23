from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class PrintingState(TypedDict):
    material_id: str
    quality_checks: List[str]
    approved: bool

def validate_media_specs(state: PrintingState):
    # Simulated validation logic for paper specs
    state['quality_checks'].append('spec_validated')
    return state

def verify_printer_compatibility(state: PrintingState):
    # Logic to ensure media aligns with machine constraints
    state['quality_checks'].append('compatibility_verified')
    state['approved'] = True
    return state

graph = StateGraph(PrintingState)
graph.add_node('validate_specs', validate_media_specs)
graph.add_node('verify_compatibility', verify_printer_compatibility)
graph.add_edge('validate_specs', 'verify_compatibility')
graph.add_edge('verify_compatibility', END)
graph.set_entry_point('validate_specs')
compiled_graph = graph.compile()
