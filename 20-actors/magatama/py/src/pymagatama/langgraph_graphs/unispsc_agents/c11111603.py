from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CarbonFiberState(TypedDict):
    material_id: str
    spec_data: dict
    validation_passed: bool
    error_log: List[str]

def validate_specs(state: CarbonFiberState):
    # Simulated technical validation for high-strength carbon fiber
    specs = state.get('spec_data', {})
    tensile = specs.get('tensile_strength_mpa', 0)
    if tensile < 3000:
        return {'validation_passed': False, 'error_log': ['Tensile strength below aerospace requirements']}
    return {'validation_passed': True}

def process_procurement(state: CarbonFiberState):
    # Logic for dual-use export control compliance check
    print(f'Processing procurement for {state['material_id']}')
    return {'validation_passed': True}

builder = StateGraph(CarbonFiberState)
builder.add_node('validate', validate_specs)
builder.add_node('process', process_procurement)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()