from typing import TypedDict
from langgraph.graph import StateGraph, END

class CentrifugeState(TypedDict):
    rpm: int
    temp: float
    calibrated: bool

def validate_specs(state: CentrifugeState):
    assert 5000 <= state['rpm'] <= 20000, 'RPM out of safe range'
    return {'calibrated': True}

def audit_risk(state: CentrifugeState):
    return {'status': 'approved' if state['temp'] < 4 else 'warning'}

graph = StateGraph(CentrifugeState)
graph.add_node('validate', validate_specs)
graph.add_node('audit', audit_risk)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph = graph.compile()
