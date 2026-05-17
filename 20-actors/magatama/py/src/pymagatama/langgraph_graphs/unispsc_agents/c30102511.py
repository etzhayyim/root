from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BronzeState(TypedDict):
    thickness_mm: float
    alloy_grade: str
    material_certified: bool
    validation_logs: List[str]

def validate_specs(state: BronzeState):
    logs = []
    if state['thickness_mm'] <= 0: logs.append('Invalid thickness')
    if not state['alloy_grade']: logs.append('Missing alloy grade')
    return {'validation_logs': logs}

def check_certification(state: BronzeState):
    return {'material_certified': state['material_certified']}

graph = StateGraph(BronzeState)
graph.add_node('validate', validate_specs)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()