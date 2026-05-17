from typing import TypedDict
from langgraph.graph import StateGraph, END
class WaterAnalyzerState(TypedDict):
    spec_data: dict
    validation_passed: bool
def validate_specs(state: WaterAnalyzerState):
    required = ['measurement_range', 'accuracy']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}
builder = StateGraph(WaterAnalyzerState)
builder.add_node('validate', validate_specs)
builder.set_entry_point('validate')
builder.add_edge('validate', END)
graph = builder.compile()