from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LampBaseState(TypedDict):
    spec_data: dict
    validation_log: List[str]
    is_compliant: bool

def validate_lamp_base(state: LampBaseState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if not specs.get('voltage_rating'):
        logs.append('Missing required voltage rating')
        compliant = False
    if 'UL_certified' not in specs:
        logs.append('Warning: Safety certification missing')
    return {'validation_log': logs, 'is_compliant': compliant}

workflow = StateGraph(LampBaseState)
workflow.add_node('validator', validate_lamp_base)
workflow.set_entry_point('validator')
workflow.add_edge('validator', END)
graph = workflow.compile()