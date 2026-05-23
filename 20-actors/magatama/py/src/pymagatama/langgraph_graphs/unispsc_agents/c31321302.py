from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    material_spec: dict
    validation_passed: bool
    compliance_report: str

def validate_materials(state: AssemblyState):
    # Basic logic to verify carbon steel grades
    grade = state['material_spec'].get('grade', 'unknown')
    is_valid = grade in ['ASTM A36', 'AISI 1018']
    return {'validation_passed': is_valid}

def generate_report(state: AssemblyState):
    report = 'Validation passed' if state['validation_passed'] else 'Invalid material grade'
    return {'compliance_report': report}

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_materials)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()
