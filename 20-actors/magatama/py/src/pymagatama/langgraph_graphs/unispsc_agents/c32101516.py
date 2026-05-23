from typing import TypedDict
from langgraph.graph import StateGraph, END

class CirculatorState(TypedDict):
    specs: dict
    validation_log: list
    compliant: bool

def validate_specs(state: CirculatorState):
    log = []
    required = ['Frequency Range', 'Insertion Loss', 'Isolation']
    compliance = all(key in state['specs'] for key in required)
    log.append('Specs validated') if compliance else log.append('Missing specs')
    return {'validation_log': log, 'compliant': compliance}

def export_review(state: CirculatorState):
    if state.get('compliant'):
        state['validation_log'].append('Dual-use export screening initiated')
    return state

graph = StateGraph(CirculatorState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', export_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()
