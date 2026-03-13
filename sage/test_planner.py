import asyncio
import logging
from core.nodes.planner import planner_node

logging.basicConfig(level=logging.DEBUG)

async def main():
    state = {
        'subject': 'NLP', 
        'unit_number': 1, 
        'unit_title': 'Unit 1', 
        'all_topics': ['Intro to NLP', 'Tokenization']
    }
    
    # We want to see EXACTLY what it's trying to parse
    from core.nodes.planner import _extract_json_list
    import urllib.request
    
    # Actually just run the planner and see what it raises
    try:
        final_state = await planner_node(state)
        print("Final clusters:", final_state.get('clusters'))
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
