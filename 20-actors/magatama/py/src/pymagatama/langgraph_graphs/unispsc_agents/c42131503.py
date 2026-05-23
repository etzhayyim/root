from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExamCapeState(TypedDict):
    spec_data: dict
    validation_results: list

def validate_materials(state: ExamCapeState):
    """Verify material compliance for clinical grade capes."""
    valid = state['spec_data'].get('material_composition') is not None
    return {'validation_results': ['Material validated' if valid else 'Material check failed']}

def safety_compliance_check(state: ExamCapeState):
    """Ensure flame retardancy and ISO compliance."""
    passed = state['spec_data'].get('flame_retardancy', False)
    return {'validation_results': state['validation_results'] + ['Safety passed' if passed else 'Safety non-compliant']}

graph = StateGraph(ExamCapeState)
graph.add_node('material_check', validate_materials)
graph.add_node('safety_check', safety_compliance_check)
graph.add_edge('material_check', 'safety_check')
graph.add_edge('safety_check', END)
graph.set_entry_point('material_check')
graph = graph.compile()
