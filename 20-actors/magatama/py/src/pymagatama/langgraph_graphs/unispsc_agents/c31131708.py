from typing import TypedDict
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    spec_data: dict
    validation_status: str
    compliance_report: str

def validate_materials(state: ForgingState):
    m_grade = state['spec_data'].get('grade')
    status = 'PASS' if m_grade in ['Grade 5', 'Ti-6Al-4V'] else 'FAIL'
    return {'validation_status': status}

def generate_report(state: ForgingState):
    report = f'Validation for {state.get("validation_status")} complete.'
    return {'compliance_report': report}

graph = StateGraph(ForgingState)
graph.add_node('validate', validate_materials)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()