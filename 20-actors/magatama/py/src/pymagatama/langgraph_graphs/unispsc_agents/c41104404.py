from typing import TypedDict
from langgraph.graph import StateGraph, END

class BODSpecState(TypedDict):
    temp_range: str
    capacity_l: float
    compliance_ok: bool
    validation_log: list

def validate_specs(state: BODSpecState):
    log = []
    if not (0 <= float(state['temp_range'].split('-')[0]) <= 20): log.append('Temp Error')
    if state['capacity_l'] < 50: log.append('Capacity too low')
    return {'validation_log': log, 'compliance_ok': len(log) == 0}

graph = StateGraph(BODSpecState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()