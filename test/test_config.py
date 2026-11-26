"""Тесты парсинга docs.yml → Pydantic-модели."""
import re
import pytest
from pathlib import Path

from llm_docs_gen.models import CmdArg, ContentItem, DocItem, DocsConfig, ProjectConfig
from llm_docs_gen.rendering import render_item

def test_render_item_format(tmp_path: Path):
    (tmp_path / "a.yml").write_text("key: value\n")
    cfg = ProjectConfig(title="t", path=str(tmp_path), docs="docs")
    item = DocItem(
        item="i", render=1, file="OUT.md", description="desc",
        content=[ContentItem(cmd="cat", args="a.yml", title="My title")],
    )
    md = render_item(item, cfg)

    assert md.startswith(f"path: {tmp_path}/docs/OUT.md")  # 1. docs в path
    assert re.search(r"\n\n-{3,}\n\n", md)                  # 2. линия-разделитель
    assert "## My title\n\n```bash\n" in md                 # 3. title как ##

# ── CmdArg ──────────────────────────────────────────────

class TestCmdArg:
    def test_flag_only(self):
        """{'flag': 'a'} → CmdArg(flag='a', value=None)"""
        a = CmdArg.parse({"flag": "a"})
        assert a.flag == "a"
        assert a.value is None

    def test_flag_with_value(self):
        """{'flag': 'I', 'value': 'venv|git'} → оба поля"""
        a = CmdArg.parse({"flag": "I", "value": "venv|git"})
        assert a.flag == "I"
        assert a.value == "venv|git"

    def test_plain_string(self):
        """Строка 'docker-compose.yml' → CmdArg(value='...')"""
        a = CmdArg.parse("docker-compose.yml")
        assert a.flag is None
        assert a.value == "docker-compose.yml"


# ── ContentItem.resolved_args ──────────────────────────

class TestContentItem:
    def test_tree_args(self):
        """tree -a -I 'venv|git' → ['-a', '-I', 'venv|git']"""
        c = ContentItem(
            cmd="tree",
            args=[{"flag": "a"}, {"flag": "I"}, {"value": "venv|git"}],
        )
        assert c.resolved_args == ["-a", "-I", "venv|git"]

    def test_cat_args(self):
        """cat docker-compose.yml → ['docker-compose.yml']"""
        c = ContentItem(cmd="cat", args=["docker-compose.yml"])
        assert c.resolved_args == ["docker-compose.yml"]

    def test_multiple_files(self):
        """cat a.yml b.yml → ['a.yml', 'b.yml']"""
        c = ContentItem(cmd="cat", args=["a.yml", "b.yml"])
        assert c.resolved_args == ["a.yml", "b.yml"]


# ── DocItem + DocsConfig ───────────────────────────────

class TestDocsConfig:
    @pytest.fixture
    def sample_yaml(self, tmp_path: Path) -> Path:
        """Минимальный docs.yml во временной директории."""
        content = """\
version: "1.0"
project:
  title: test
  path: /tmp/fake
  docs: docs
  items:
    - item: infra
      render: 10
      file: INFRA.md
      description: test infra
      content:
        - cmd: cat
          args: [docker-compose.yml]
          title: compose
    - item: tree
      render: 99
      file: TREE.md
      content:
        - cmd: tree
          args:
            - flag: a
            - flag: I
              value: ".git|.venv"
"""
        p = tmp_path / "docs.yml"
        p.write_text(content)
        return p

    def test_load(self, sample_yaml: Path):
        cfg = DocsConfig.load(sample_yaml)
        assert cfg.version == "1.0"
        assert cfg.project is not None
        assert len(cfg.project["items"]) == 2

    def test_render_order(self, sample_yaml: Path):
        cfg = DocsConfig.load(sample_yaml)
        assert cfg.project is not None, "Project config missing in YAML"
        # from llm_docs_gen.config import ProjectConfig
        proj = ProjectConfig(**cfg.project)
        items = proj.sorted_items
        assert items[0].render == 10
        assert items[1].render == 99


##############################################
class TestContentItemEdgeCases:
    def test_args_as_string(self):
        """args: docker-compose.yml  (строка, не список)"""
        c = ContentItem(cmd="cat", args="docker-compose.yml")
        assert c.resolved_args == ["docker-compose.yml"]

    def test_args_as_list_of_strings(self):
        """args: [a.yml, b.yml]"""
        c = ContentItem(cmd="cat", args=["a.yml", "b.yml"])
        assert c.resolved_args == ["a.yml", "b.yml"]

    def test_args_as_list_of_dicts(self):
        """args: [{flag: a}, {flag: I, value: 'venv|git'}]"""
        c = ContentItem(cmd="tree", args=[{"flag": "a"}, {"flag": "I", "value": "venv|git"}])
        assert c.resolved_args == ["-a", "-I", "venv|git"]

    def test_empty_args(self):
        c = ContentItem(cmd="pwd", args=[])
        assert c.resolved_args == []


class TestDocItem:
    def test_render_sort(self):
        items = [
            DocItem(item="b", render=99, file="B.md"),
            DocItem(item="a", render=10, file="A.md"),
        ]
        # from llm_docs_gen.config import ProjectConfig
        proj = ProjectConfig(title="t", path="/tmp", docs="docs", items=items)
        sorted_items = proj.sorted_items
        assert sorted_items[0].item == "a"
        assert sorted_items[1].item == "b"


class TestTildeExpansion:
    def test_path_expanduser(self):
        """path: ~/projects/dbt → /home/user/projects/dbt"""
        # from pathlib import Path
        raw = "~/projects/dbt"
        expanded = Path(raw).expanduser()
        assert "~" not in str(expanded)   
