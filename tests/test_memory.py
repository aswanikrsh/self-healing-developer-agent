
from agent.memory import MemoryManager


def test_memory_manager_initializes():
    manager = MemoryManager()

    assert manager is not None
    assert manager.store is not None


def test_chroma_collection_exists():
    manager = MemoryManager()

    assert manager.store.collection is not None


def test_memory_count_is_available():
    manager = MemoryManager()

    count = manager.store.count()

    assert isinstance(count, int)
    assert count >= 0
