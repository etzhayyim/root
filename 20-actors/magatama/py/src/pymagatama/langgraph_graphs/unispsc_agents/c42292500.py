from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalInstrumentState(TypedDict):
    instrument_type: str
    material_spec: str
    is_compliant: bool

def validate_material(state: SurgicalInstrumentState):
    state['is_compliant'] = state.get('material_spec') == 'Surgical-Grade-Steel'
    return state

def process_instrument(state: SurgicalInstrumentState):
    print(f'Processing {state["instrument_type"]} for clinical use...')
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(SurgicalInstrumentState)
graph.add_node('validate', validate_material)
graph.add_node('process', process_instrument)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
