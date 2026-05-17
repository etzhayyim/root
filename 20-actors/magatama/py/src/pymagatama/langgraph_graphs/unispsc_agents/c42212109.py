from typing import TypedDict
from langgraph.graph import StateGraph, END
class AdaptiveToolState(TypedDict):
    tool_id: str
    accessibility_score: float
    safety_check_passed: bool
def validate_accessibility(state: AdaptiveToolState):
    state['accessibility_score'] = 1.0 if state.get('tool_id') else 0.0
    return 'check_safety'
def check_safety(state: AdaptiveToolState):
    state['safety_check_passed'] = True
    return END
graph = StateGraph(AdaptiveToolState)
graph.add_node('validate', validate_accessibility)
graph.add_node('check_safety', check_safety)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()