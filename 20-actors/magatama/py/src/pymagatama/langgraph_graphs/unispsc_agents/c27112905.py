from typing import TypedDict
from langgraph.graph import StateGraph, END

class OilCanState(TypedDict):
    capacity: float
    material: str
    is_leak_tested: bool

def validate_specs(state: OilCanState):
    if state['capacity'] <= 0:
        raise ValueError('Invalid capacity')
    return {'is_leak_tested': True}

def assembly_workflow(state: OilCanState):
    print('Assembling oil can components...')
    return state

graph = StateGraph(OilCanState)
graph.add_node('validate', validate_specs)
graph.add_node('assemble', assembly_workflow)
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph.set_entry_point('validate')
graph = graph.compile()
