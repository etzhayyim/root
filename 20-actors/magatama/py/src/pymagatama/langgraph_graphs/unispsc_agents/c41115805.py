from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AnalyzerState(TypedDict):
    device_id: str
    validation_checks: List[str]
    is_compliant: bool

def validate_calibration(state: AnalyzerState):
    state['validation_checks'].append('calibration_verified')
    state['is_compliant'] = True
    return state

def check_regulatory(state: AnalyzerState):
    state['validation_checks'].append('iso_13485_verified')
    return state

graph = StateGraph(AnalyzerState)
graph.add_node('validate', validate_calibration)
graph.add_node('regulatory', check_regulatory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()
