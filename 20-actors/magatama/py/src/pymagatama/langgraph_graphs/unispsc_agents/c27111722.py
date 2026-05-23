from typing import TypedDict
from langgraph.graph import StateGraph, END

class DieStockState(TypedDict):
    material_specs: dict
    validation_passed: bool

def validate_tool_specs(state: DieStockState):
    hardness = state['material_specs'].get('hardness_hrc', 0)
    state['validation_passed'] = 45 <= hardness <= 60
    return state

workflow = StateGraph(DieStockState)
workflow.add_node('validation', validate_tool_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
