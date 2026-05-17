from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EndoscopyPrinterState(TypedDict):
    device_id: str
    validation_passed: bool
    compliance_docs: List[str]

def validate_specs(state: EndoscopyPrinterState):
    # Simulate validation logic for medical device compliance
    state['validation_passed'] = True
    return state

def generate_procurement_report(state: EndoscopyPrinterState):
    print(f'Generating report for {state['device_id']}')
    return state

graph = StateGraph(EndoscopyPrinterState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_procurement_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()