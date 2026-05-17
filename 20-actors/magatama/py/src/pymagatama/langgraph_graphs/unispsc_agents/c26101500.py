from typing import TypedDict
from langgraph.graph import StateGraph, END
class EngineState(TypedDict):
    spec: dict
    validated: bool
    engine_type: str
def validate_specs(state: EngineState):
    state['validated'] = 'horsepower_rating' in state['spec'] and 'emission_certification' in state['spec']
    return state
def check_export_controls(state: EngineState):
    print(f'Checking dual-use controls for {state.get('engine_type')}')
    return state
graph = StateGraph(EngineState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_controls)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()