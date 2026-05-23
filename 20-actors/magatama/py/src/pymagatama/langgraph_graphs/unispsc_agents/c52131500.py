from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CurtainState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: CurtainState):
    errors = []
    if 'flame_retardancy' not in state['specs']:
        errors.append('Flame retardancy specification missing')
    if state.get('specs', {}).get('width', 0) <= 0:
        errors.append('Invalid dimensions provided')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def finalize_procurement(state: CurtainState):
    return {'validation_passed': True}

graph = StateGraph(CurtainState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
