from typing import TypedDict
from langgraph.graph import StateGraph, END
class InkProcurementState(TypedDict):
    spec_sheet: dict
    is_hazardous: bool
    validation_passed: bool
def validate_msds(state: InkProcurementState):
    state['is_hazardous'] = 'SDS' in state['spec_sheet']
    return {'validation_passed': True}
def final_review(state: InkProcurementState):
    return {'validation_passed': state.get('is_hazardous', False)}
graph = StateGraph(InkProcurementState)
graph.add_node('validate', validate_msds)
graph.add_node('review', final_review)
graph.set_entry_point('validate')
graph.add_edge('validate', 'review')
graph.add_edge('review', END)
graph = graph.compile()
