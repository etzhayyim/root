from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class LatheState(TypedDict):
    commodity_code: str
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: LatheState):
    errors = []
    if 'machining_accuracy_tolerance' not in state['spec_data']:
        errors.append('Missing accuracy tolerance')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def process_procurement(state: LatheState):
    if state['is_compliant']:
        print('Lathe procurement workflow ready.')
    return {}

graph = StateGraph(LatheState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()