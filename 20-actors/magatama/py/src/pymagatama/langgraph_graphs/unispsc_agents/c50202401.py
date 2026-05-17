from typing import TypedDict
from langgraph.graph import StateGraph, END

class JuiceState(TypedDict):
    brics_value: float
    safety_clearance: bool
    is_compliant: bool

def validate_quality(state: JuiceState):
    compliant = state['brics_value'] >= 10.0 and state['safety_clearance']
    return {'is_compliant': compliant}

graph = StateGraph(JuiceState)
graph.add_node('qc_check', validate_quality)
graph.set_entry_point('qc_check')
graph.add_edge('qc_check', END)
graph = graph.compile()