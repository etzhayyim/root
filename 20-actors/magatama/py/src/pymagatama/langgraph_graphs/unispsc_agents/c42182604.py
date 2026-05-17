from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExamLightState(TypedDict):
    lumens: float
    iso_compliant: bool
    is_approved: bool

def validate_specs(state: ExamLightState):
    if state['lumens'] < 5 or state['lumens'] > 50:
        return {'is_approved': False}
    return {'is_approved': state['iso_compliant']}

graph = StateGraph(ExamLightState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()