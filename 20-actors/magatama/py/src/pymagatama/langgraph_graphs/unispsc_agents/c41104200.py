from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabWaterState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_specs(state: LabWaterState):
    required = ['Resistivity', 'TOC Level']
    logs = []
    compliant = True
    for field in required:
        if field not in state['spec_data']:
            logs.append(f'Missing spec: {field}')
            compliant = False
    return {'validation_log': logs, 'is_compliant': compliant}

workflow = StateGraph(LabWaterState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()