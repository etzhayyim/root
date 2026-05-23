from typing import TypedDict
from langgraph.graph import StateGraph, END

class HistoryUnitState(TypedDict):
    material_content: str
    compliance_report: str
    approved: bool

def validate_curriculum_alignment(state: HistoryUnitState):
    state['approved'] = 'curriculum_std' in state['material_content']
    return {'approved': state['approved']}

def process_content(state: HistoryUnitState):
    state['compliance_report'] = 'Validated historical accuracy and age appropriateness' if state['approved'] else 'Review required'
    return {'compliance_report': state['compliance_report']}

graph = StateGraph(HistoryUnitState)
graph.add_node('validate', validate_curriculum_alignment)
graph.add_node('process', process_content)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
