from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RhythmStickState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    approved: bool

def validate_materials(state: RhythmStickState):
    wood = state['spec_data'].get('wood_type')
    results = state.get('validation_results', [])
    if wood in ['rosewood', 'maple', 'beech']:
        results.append('Material verified')
    return {'validation_results': results}

def check_safety(state: RhythmStickState):
    results = state.get('validation_results', [])
    if state['spec_data'].get('safety_standard_compliance'):
        results.append('Safety compliant')
    return {'validation_results': results, 'approved': len(results) >= 2}

graph = StateGraph(RhythmStickState)
graph.add_node('validate_materials', validate_materials)
graph.add_node('check_safety', check_safety)
graph.set_entry_point('validate_materials')
graph.add_edge('validate_materials', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()