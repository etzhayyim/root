from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class JuiceState(TypedDict):
    brics_level: float
    has_safety_cert: bool
    passed_inspection: bool

def validate_quality(state: JuiceState):
    if state['brics_level'] < 11.0:
        return 'REJECT'
    return 'APPROVE'

def check_compliance(state: JuiceState):
    return {'passed_inspection': state['has_safety_cert']}

graph = StateGraph(JuiceState)
graph.add_node('validate', validate_quality)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'validate')
graph.add_edge('validate', END)
app = graph.compile()
