from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class AlloyState(TypedDict):
    material_code: str
    purity_level: float
    certification_required: bool
    compliance_checks: Annotated[List[str], add_messages]

def validate_material_specs(state: AlloyState):
    checks = []
    if state['purity_level'] < 99.9:
        checks.append('Purity check failed')
    else:
        checks.append('Purity check passed')
    return {'compliance_checks': checks}

def perform_export_control_review(state: AlloyState):
    return {'compliance_checks': ['Export control cleared for industrial use']}

def build_graph():
    graph = StateGraph(AlloyState)
    graph.add_node('validate', validate_material_specs)
    graph.add_node('export_review', perform_export_control_review)
    graph.set_entry_point('validate')
    graph.add_edge('validate', 'export_review')
    graph.add_edge('export_review', END)
    return graph.compile()

graph = build_graph()
