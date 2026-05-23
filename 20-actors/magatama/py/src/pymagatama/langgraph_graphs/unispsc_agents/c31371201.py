from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastableState(TypedDict):
    material_spec: dict
    validation_status: bool
    compliance_report: str

def validate_density(state: CastableState):
    density = state['material_spec'].get('density', 0)
    status = density > 2000
    return {'validation_status': status}

def generate_report(state: CastableState):
    report = 'Validated' if state['validation_status'] else 'Failed specification density'
    return {'compliance_report': report}

graph = StateGraph(CastableState)
graph.add_node('validate', validate_density)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
