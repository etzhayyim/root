from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FlightInstState(TypedDict):
    part_number: str
    certification_docs: List[str]
    compliance_status: bool

def validate_specs(state: FlightInstState):
    # Simulate high-precision CAD and certification validation
    is_compliant = 'TSO' in str(state['certification_docs'])
    return {**state, 'compliance_status': is_compliant}

def export_review(state: FlightInstState):
    # Placeholder for dual-use export control logic
    return {**state, 'compliance_status': state['compliance_status'] and True}

graph = StateGraph(FlightInstState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_review)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()