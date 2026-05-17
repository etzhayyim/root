from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MicroformState(TypedDict):
    part_number: str
    spec_compliance: bool
    validation_logs: List[str]

def validate_specs(state: MicroformState):
    state['validation_logs'].append('Checking optical tolerance...')
    state['spec_compliance'] = True
    return state

def generate_report(state: MicroformState):
    state['validation_logs'].append('Generating procurement compliance report...')
    return state

graph = StateGraph(MicroformState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()