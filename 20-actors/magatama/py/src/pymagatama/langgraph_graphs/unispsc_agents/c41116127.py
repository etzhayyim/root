from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    item_name: str
    batch_id: str
    temp_control_check: bool
    validation_passed: bool

def validate_batch(state: ReagentState):
    # Simulate stringent biochemical validation
    passed = state['temp_control_check'] and len(state['batch_id']) > 5
    return {'validation_passed': passed}

def route_by_status(state: ReagentState):
    return 'pass' if state['validation_passed'] else 'fail'

graph = StateGraph(ReagentState)
graph.add_node('validator', validate_batch)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph.compile()