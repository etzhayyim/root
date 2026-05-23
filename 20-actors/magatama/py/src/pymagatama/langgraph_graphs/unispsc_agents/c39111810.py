from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StarterState(TypedDict):
    specifications: dict
    is_compliant: bool
    validation_log: List[str]

def validate_specs(state: StarterState):
    specs = state['specifications']
    logs = []
    compliant = True
    if 'voltage' not in specs or 'wattage' not in specs:
        logs.append('Missing mandatory voltage or wattage specs')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': logs}

def final_check(state: StarterState):
    return {'validation_log': state['validation_log'] + ['Processing complete']}

graph = StateGraph(StarterState)
graph.add_node('validate', validate_specs)
graph.add_node('final', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph = graph.compile()
