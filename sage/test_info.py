import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from config import NOTEBOOKLM_NOTEBOOK_ID

async def test_infographic():
    from notebooklm import NotebookLMClient
    print(f"Testing with Notebook ID: {NOTEBOOKLM_NOTEBOOK_ID}")
    
    async with await NotebookLMClient.from_storage() as client:
        try:
            print("Requesting infographic...")
            res = await client.artifacts.generate_infographic(
                NOTEBOOKLM_NOTEBOOK_ID,
                instructions="Test infographic"
            )
            print("Response type:", type(res))
            print("Response:", res)
            
            # If res is a string, it's the task/artifact ID
            # If res is an object, see if it has task_id
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_infographic())
