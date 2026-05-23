from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AssemblyState(TypedDict):
    part_specs: dict
    validation_results: List[str]
    approved: bool

def validate_specs(state: AssemblyState):
    grades = state['part_specs'].get('grade')
    results = []
    if not grades: results.append('Missing material grade')
    return {'validation_results': results, 'approved': len(results) == 0}

def ndt_check(state: AssemblyState):
    if state['approved']:
        print('Performing Ultrasonic Testing...')
    return state

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_specs)
graph.add_node('ndt', ndt_check)
graph.add_edge('validate', 'ndt')
graph.add_edge('ndt', END)
graph.set_entry_point('validate')
graph = graph.compile()
