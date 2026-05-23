from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    specs: dict
    approved: bool
    validation_report: str

def validate_material(state: CastState):
    hardness = state['specs'].get('hardness', 0)
    state['approved'] = hardness > 200
    return {'approved': state['approved']}

def generate_report(state: CastState):
    state['validation_report'] = 'High-grade iron graphite casting validated.'
    return {'validation_report': state['validation_report']}

graph = StateGraph(CastState)
graph.add_node('validate', validate_material)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
compile_graph = graph.compile()
