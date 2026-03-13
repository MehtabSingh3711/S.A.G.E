import asyncio
import sys
from pathlib import Path

# Add current dir to path
sys.path.insert(0, str(Path.cwd()))

async def test_auth():
    print("Attempting to load NotebookLM storage...")
    try:
        from notebooklm import NotebookLMClient
        client = await NotebookLMClient.from_storage()
        print("Storage loaded successfully!")
        
        async with client:
            print("Browser launched and session verified.")
            # Just list notebooks to prove it works
            notebooks = await client.notebooks.list()
            print(f"Success! Found {len(notebooks)} notebooks.")
            for nb in notebooks[:3]:
                print(f" - {nb.title} ({nb.id})")
                
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        print("\nPossible fixes:")
        print("1. Run 'notebooklm login' again")
        print("2. Ensure Chrome/Edge is installed")
        print("3. Check internet connection")

if __name__ == "__main__":
    asyncio.run(test_auth())
