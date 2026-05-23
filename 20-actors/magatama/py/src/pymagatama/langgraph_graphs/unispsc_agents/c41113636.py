from typing import TypedDict
from langgraph.graph import StateGraph, END

class LevelGeneratorState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: LevelGeneratorState):
    error_log = []
    if 'frequency_range' not in state['spec_data']:
        error_log.append('Missing frequency_range')

    validated = len(error_log) == 0
    return {'validated': validated, 'error_log': error_log}

workflow = StateGraph(LevelGeneratorState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
