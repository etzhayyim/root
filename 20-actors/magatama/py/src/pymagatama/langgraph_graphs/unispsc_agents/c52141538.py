from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodWarmerState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: FoodWarmerState):
    required = ['voltage', 'certification', 'max_temp']
    errors = []
    for field in required:
        if field not in state['spec_data']:
            errors.append(f'Missing {field}')
    return {'validated': len(errors) == 0, 'error_log': errors}

def safety_check(state: FoodWarmerState):
    # Business logic for electrical appliance safety protocols
    print('Running thermal cutoff validation...')
    return {'validated': state['validated']}

graph = StateGraph(FoodWarmerState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()