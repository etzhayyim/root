from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class GrainProcessingState(TypedDict):
    grain_batch_id: str
    moisture_level: float
    inspection_passed: bool
    process_steps: Annotated[Sequence[str], operator.add]

def validate_moisture(state: GrainProcessingState):
    passed = state['moisture_level'] <= 14.0
    return {'inspection_passed': passed, 'process_steps': ['moisture_check_completed']}

def milling_process(state: GrainProcessingState):
    if state['inspection_passed']:
        return {'process_steps': ['mechanical_milling_done', 'polishing_done']}
    return {'process_steps': ['milling_skipped_due_to_moisture']}

def packaging_process(state: GrainProcessingState):
    return {'process_steps': ['vacuum_sealing_completed', 'final_quality_audit']}

graph = StateGraph(GrainProcessingState)
graph.add_node('validate', validate_moisture)
graph.add_node('mill', milling_process)
graph.add_node('package', packaging_process)
graph.set_entry_point('validate')
graph.add_edge('validate', 'mill')
graph.add_edge('mill', 'package')
graph.add_edge('package', END)
graph = graph.compile()
