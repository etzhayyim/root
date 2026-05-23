from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    purity_level: float
    safety_check_passed: bool
    process_steps: List[str]

def validate_material(state: ProcessingState) -> ProcessingState:
    if state['purity_level'] > 99.9:
        state['safety_check_passed'] = True
        state['process_steps'].append('Validation Complete')
    else:
        state['safety_check_passed'] = False
        state['process_steps'].append('Validation Failed: Purity too low')
    return state

def refine_compound(state: ProcessingState) -> ProcessingState:
    if state['safety_check_passed']:
        state['process_steps'].append('Thermal Refining Initiated')
    return state

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_material)
graph.add_node('refine', refine_compound)
graph.add_edge('validate', 'refine')
graph.add_edge('refine', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
