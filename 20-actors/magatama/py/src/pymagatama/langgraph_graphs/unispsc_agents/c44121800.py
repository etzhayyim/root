from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CorrectionMediaState(TypedDict):
    item_name: str
    specifications: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: CorrectionMediaState):
    errors = []
    if not state['specifications'].get('non_toxic_certification'):
        errors.append('Missing safety certification')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def route_by_validation(state: CorrectionMediaState):
    return 'process' if state['validation_passed'] else END

def process_procurement(state: CorrectionMediaState):
    print(f'Processing procurement for: {state["item_name"]}')
    return {'validation_passed': True}

graph = StateGraph(CorrectionMediaState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
