from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    batch_id: str
    brix_value: float
    is_compliant: bool

def validate_brix(state: ProcessingState):
    # Threshold: 60-68 Brix for Mandarin concentrate
    state['is_compliant'] = 60 <= state['brix_value'] <= 68
    return state

def check_quality(state: ProcessingState):
    print(f'Final validation status for {state['batch_id']}: {state['is_compliant']}')
    return state

graph = StateGraph(ProcessingState)
graph.add_node('validate_brix', validate_brix)
graph.add_node('check_quality', check_quality)
graph.set_entry_point('validate_brix')
graph.add_edge('validate_brix', 'check_quality')
graph.add_edge('check_quality', END)
app = graph.compile()