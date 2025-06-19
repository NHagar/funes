"""Tests for memory tools functionality."""

from pathlib import Path

import pytest
from pyfakefs.fake_filesystem_unittest import TestCase

from memchat.tools import (
    execute_tool_call,
    list_memory_files,
    read_memory_file,
)


class TestMemoryTools(TestCase):
    """Test memory tools with fake filesystem."""

    def setUp(self):
        """Set up fake filesystem."""
        self.setUpPyfakefs()

        # Create test memory directory and files
        self.test_mem_dir = Path("/test/memory")
        self.test_mem_dir.mkdir(parents=True)

        # Override MEM_DIR for testing
        import memchat.tools

        memchat.tools.MEM_DIR = self.test_mem_dir

        # Create test files
        (self.test_mem_dir / "file1.txt").write_text("Content of file 1")
        (self.test_mem_dir / "file2.md").write_text(
            "# Markdown content\n\nSome text here"
        )

        # Create subdirectory with file
        subdir = self.test_mem_dir / "subdir"
        subdir.mkdir()
        (subdir / "nested.txt").write_text("Nested file content")

        # Create hidden file (should be ignored)
        (self.test_mem_dir / ".hidden").write_text("Hidden content")

    def test_list_memory_files_empty(self):
        """Test listing files from empty directory."""
        empty_dir = Path("/empty/memory")
        empty_dir.mkdir(parents=True)

        import memchat.tools

        original_dir = memchat.tools.MEM_DIR
        memchat.tools.MEM_DIR = empty_dir

        try:
            files = list_memory_files()
            assert files == []
        finally:
            memchat.tools.MEM_DIR = original_dir

    def test_list_memory_files_with_content(self):
        """Test listing files with content."""
        files = list_memory_files()
        expected = ["file1.txt", "file2.md", "subdir/nested.txt"]
        assert sorted(files) == sorted(expected)

    def test_read_memory_file_success(self):
        """Test reading existing file."""
        content = read_memory_file("file1.txt")
        assert content == "Content of file 1"

        content = read_memory_file("file2.md")
        assert "# Markdown content" in content

        content = read_memory_file("subdir/nested.txt")
        assert content == "Nested file content"

    def test_read_memory_file_not_found(self):
        """Test reading non-existent file."""
        with pytest.raises(FileNotFoundError):
            read_memory_file("nonexistent.txt")

    def test_read_memory_file_directory(self):
        """Test reading directory path."""
        with pytest.raises(ValueError, match="Path is not a file"):
            read_memory_file("subdir")

    def test_read_memory_file_path_traversal(self):
        """Test path traversal protection."""
        with pytest.raises(ValueError, match="Path outside memory directory"):
            read_memory_file("../outside.txt")

        with pytest.raises(ValueError, match="Path outside memory directory"):
            read_memory_file("/etc/passwd")

    def test_execute_tool_call_list(self):
        """Test executing list_memory_files tool call."""
        result = execute_tool_call("list_memory_files", {})
        assert "file1.txt" in result
        assert "file2.md" in result
        assert "subdir/nested.txt" in result

    def test_execute_tool_call_read(self):
        """Test executing read_memory_file tool call."""
        result = execute_tool_call("read_memory_file", {"path": "file1.txt"})
        assert "Contents of file1.txt:" in result
        assert "Content of file 1" in result

    def test_execute_tool_call_read_error(self):
        """Test executing read with error."""
        result = execute_tool_call("read_memory_file", {"path": "nonexistent.txt"})
        assert "Error reading nonexistent.txt:" in result

    def test_execute_tool_call_missing_args(self):
        """Test executing read without required args."""
        result = execute_tool_call("read_memory_file", {})
        assert "Error: 'path' parameter is required" in result

    def test_execute_tool_call_unknown_tool(self):
        """Test executing unknown tool."""
        result = execute_tool_call("unknown_tool", {})
        assert "Error: Unknown tool 'unknown_tool'" in result


def test_memory_tools_import():
    """Test that tools can be imported correctly."""
    from memchat.tools import MEMORY_TOOLS, list_memory_files, read_memory_file

    assert len(MEMORY_TOOLS) == 2
    assert MEMORY_TOOLS[0]["function"]["name"] == "list_memory_files"
    assert MEMORY_TOOLS[1]["function"]["name"] == "read_memory_file"

    # Functions should be callable
    assert callable(list_memory_files)
    assert callable(read_memory_file)
