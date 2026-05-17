from typing import TypedDict
from langgraph.graph import StateGraph, END

class TitaniumState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: TitaniumState):
    grade = state['specs'].get('ASTM_Grade')
    valid = grade in ['Grade 5', 'Grade 2', 'Ti-6Al-4V']
    return {'validation_passed': valid, 'compliance_report': 'Validated' if valid else 'Invalid Grade'}

def check_compliance(state: TitaniumState):
    return {'compliance_report': 'Export control and MTR verification complete'}

graph = StateGraph(TitaniumState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()