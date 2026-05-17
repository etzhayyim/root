from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    part_id: str
    validation_passed: bool
    logs: List[str]

def validate_part(state: ProcessingState) -> ProcessingState:
    print(f'Validating component: {state['part_id']}')
    return {'validation_passed': True, 'logs': state.get('logs', []) + ['Component passsed hardware audit']}

def route_procurement(state: ProcessingState) -> str:
    return 'VALIDATE' if state['validation_passed'] else END

graph = StateGraph(ProcessingState)
graph.add_node('VALIDATE', validate_part)
graph.set_entry_point('VALIDATE')
graph.add_edge('VALIDATE', END)
graph = graph.compile()