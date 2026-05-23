from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FlashMemoryState(TypedDict):
    part_number: str
    specifications: dict
    validation_results: List[str]
    approved: bool

def validate_specs(state: FlashMemoryState):
    specs = state['specifications']
    results = []
    if specs.get('capacity', 0) < 0:
        results.append('Invalid capacity')
    if 'interface' not in specs:
        results.append('Missing interface type')
    return {'validation_results': results, 'approved': len(results) == 0}

def export_control_check(state: FlashMemoryState):
    # Simulate dual-use export check logic
    return {'validation_results': state['validation_results'] + ['Export control check passed']}

graph = StateGraph(FlashMemoryState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
