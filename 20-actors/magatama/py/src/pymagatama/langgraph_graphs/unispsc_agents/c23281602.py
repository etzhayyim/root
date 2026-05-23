from typing import TypedDict
from langgraph.graph import StateGraph, END

class QuenchState(TypedDict):
    temp_celsius: float
    cooling_medium: str
    is_compliant: bool

def validate_thermal_specs(state: QuenchState):
    state['is_compliant'] = state['temp_celsius'] > 0 and state['cooling_medium'] != ''
    return state

def safety_check(state: QuenchState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(QuenchState)
graph.add_node('validate', validate_thermal_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
