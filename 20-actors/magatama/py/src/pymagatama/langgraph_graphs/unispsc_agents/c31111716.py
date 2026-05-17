from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TitaniumState(TypedDict):
    specifications: dict
    validation_passed: bool
    compliance_risk: str

def validate_materials(state: TitaniumState):
    # Simulate chemical verification against ASTM standards
    state['validation_passed'] = state['specifications'].get('grade') in ['Grade 5', 'Grade 23']
    return state

def check_export_control(state: TitaniumState):
    # Dual-use risk logic
    state['compliance_risk'] = 'High' if state['specifications'].get('hardness') > 40 else 'Standard'
    return state

graph = StateGraph(TitaniumState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()