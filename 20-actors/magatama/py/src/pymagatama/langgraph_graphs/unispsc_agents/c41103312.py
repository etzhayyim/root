from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ViscoState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: ViscoState):
    required = ['range', 'temp', 'accuracy']
    result = all(k in state['spec_data'] for k in required)
    return {'validation_log': ['Specs checked'], 'is_compliant': result}

def export_review(state: ViscoState):
    if state.get('is_compliant'):
        return {'validation_log': state['validation_log'] + ['Export control check passed']}
    return {'validation_log': state['validation_log'] + ['Export control check failed']}

graph = StateGraph(ViscoState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph = graph.compile()