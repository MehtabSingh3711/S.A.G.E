"""Quick test: does the writer produce clean markdown instead of broken JSON?"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)

from core.state import TopicCluster

# Simulate a cluster with fake retrieved content
cluster = TopicCluster(
    cluster_id=1,
    topics=["Tokenization in NLP"],
    query="Explain tokenization",
    raw_answer="Tokenization is the process of breaking text into smaller units called tokens. These can be words, subwords, or characters. Common methods include whitespace splitting, BPE (Byte Pair Encoding), and WordPiece. BPE is used in GPT models while WordPiece is used in BERT.",
)

async def main():
    from core.nodes.writer import writer_node, _extract_notes_and_mermaid
    
    state = {
        "subject": "NLP",
        "unit_number": 1,
        "unit_title": "Unit 1",
        "all_topics": ["Tokenization in NLP"],
        "clusters": [cluster],
        "current_cluster_idx": 0,
        "errors": [],
        "is_complete": False,
    }
    
    result = await writer_node(state)
    
    c = result["clusters"][0]
    print("=" * 60)
    print("NOTES (first 500 chars):")
    print("=" * 60)
    print(c.notes_content[:500] if c.notes_content else "EMPTY!")
    print()
    print("=" * 60)
    print("MERMAID:")
    print("=" * 60)
    print(c.mermaid_code[:300] if c.mermaid_code else "(none)")
    print()
    
    # Check if it looks like JSON garbage
    if c.notes_content and c.notes_content.strip().startswith("{"):
        print("❌ FAIL: Output starts with { — still looks like JSON!")
    elif c.notes_content and "##" in c.notes_content:
        print("✅ PASS: Output contains markdown headers — clean notes!")
    else:
        print("⚠️  UNKNOWN: Check output manually")

if __name__ == "__main__":
    asyncio.run(main())
