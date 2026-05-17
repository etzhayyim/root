from typing import TypedDict
from langgraph.graph import StateGraph, END

class PrintingBlockState(TypedDict):
    material_info: dict
    validation_status: bool
    error_log: list[str]

def validate_material(state: PrintingBlockState) -> PrintingBlockState:
    moisture = state['material_info'].get('moisture', 10)
    if moisture > 12:
        state['validation_status'] = False
        state['error_log'].append('Moisture content exceeds maximum limit.')
    else:
        state['validation_status'] = True
    return state

def finalize_order(state: PrintingBlockState) -> PrintingBlockState:
    if state['validation_status']:
        print('Ordering process approved for wood blocks.')
    return state

graph = StateGraph(PrintingBlockState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()