from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    lot_number: str
    quality_passed: bool
    temperature_logs: List[float]
    final_status: str

def validate_quality(state: ReagentState) -> ReagentState:
    # Logic to verify quality check pass
    state['quality_passed'] = True
    return state

def check_temp_stability(state: ReagentState) -> ReagentState:
    # Logic to evaluate temperature stability logs
    if all(t < 8.0 for t in state['temperature_logs']):
        state['final_status'] = 'STABLE'
    else:
        state['final_status'] = 'EXPIRED'
    return state

graph = StateGraph(ReagentState)
graph.add_node('validate', validate_quality)
graph.add_node('check_temp', check_temp_stability)
graph.add_edge('validate', 'check_temp')
graph.add_edge('check_temp', END)
graph.set_entry_point('validate')
graph = graph.compile()
