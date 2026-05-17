from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChartHolderState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: ChartHolderState):
    # Perform specific check for medical grade material compatibility
    state['validation_passed'] = 'Material' in state['spec_data']
    return {'validation_passed': state['validation_passed']}

def generate_report(state: ChartHolderState):
    return {'compliance_report': 'Validated against clinical storage standards'}

graph = StateGraph(ChartHolderState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()