import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

async def test_studio():
    try:
        from notebooklm import NotebookLMClient
        client = await NotebookLMClient.from_storage()
        print("Methods of client:")
        for attr in dir(client):
            if not attr.startswith("_"):
                print(" -", attr)
        
        # Let's inspect client.artifacts or client.studio
        if hasattr(client, 'studio'):
            print("\nMethods of client.studio:")
            for attr in dir(client.studio):
                if not attr.startswith("_"):
                    print(" -", attr)
                    
        if hasattr(client, 'artifacts'):
            print("\nMethods of client.artifacts:")
            for attr in dir(client.artifacts):
                if not attr.startswith("_"):
                    print(" -", attr)
                    
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_studio())
