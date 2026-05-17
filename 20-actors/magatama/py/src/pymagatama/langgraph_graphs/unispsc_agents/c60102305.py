from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ReadingProgramState(TypedDict):
    program_name: str
    target_level: str
    validation_passed: bool
    errors: List[str]

def validate_curriculum(state: ReadingProgramState) -> ReadingProgramState:
    if not state.get('target_level'):
        state['errors'].append('Target level is missing')
        state['validation_passed'] = False
    else:
        state['validation_passed'] = True
    return state

def route_by_validation(state: ReadingProgramState) -> str:
    return 'process' if state['validation_passed'] else END

def finalize_procurement(state: ReadingProgramState) -> ReadingProgramState:
    print(f'Processing procurement for {state['program_name']}')
    return state

graph = StateGraph(ReadingProgramState)
graph.add_node('validate', validate_curriculum)
graph.add_node('process', finalize_procurement)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()