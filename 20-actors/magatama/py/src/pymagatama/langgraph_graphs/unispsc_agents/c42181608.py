from typing import TypedDict
from langgraph.graph import StateGraph, END

class BloodPressureAccState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_accessory_standard(state: BloodPressureAccState):
    fields = state['spec_data']
    required = ['ISO_13485_certification', 'biocompatibility_certification']
    compliant = all(fields.get(f) for f in required)
    return {'is_compliant': compliant}

workflow = StateGraph(BloodPressureAccState)
workflow.add_node('validation', validate_accessory_standard)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
