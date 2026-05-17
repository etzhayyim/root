from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_tool_specs(state: ToolState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if specs.get('motor_power', 0) < 500:
        logs.append('Insufficient motor power for professional use')
        compliant = False
    return {'validation_log': logs, 'is_compliant': compliant}

workflow = StateGraph(ToolState)
workflow.add_node('validate', validate_tool_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()