from flagrant.parser._result import ParseResult


class TestParseResultInitialization:
    def test_creates_minimal_result(self):
        result = ParseResult(args=(), command="test")

        assert result.command == "test"
        assert result.args == ()
        assert result.options == {}
        assert result.positionals == {}
        assert result.extra_args == ()
        assert result.subcommand is None

    def test_creates_result_with_options(self):
        result = ParseResult(
            args=("--verbose",),
            command="test",
            options={"verbose": True},
        )

        assert result.options["verbose"] is True

    def test_creates_result_with_positionals(self):
        result = ParseResult(
            args=("file.txt",),
            command="test",
            positionals={"files": ("file.txt",)},
        )

        assert result.positionals["files"] == ("file.txt",)


class TestParseResultSubcommandHierarchy:
    def test_single_command_has_no_subcommand(self):
        result = ParseResult(args=(), command="git")

        assert result.subcommand is None
        assert result.is_leaf is True
        assert result.has_subcommand is False

    def test_command_with_subcommand(self):
        sub = ParseResult(args=(), command="commit")
        result = ParseResult(args=(), command="git", subcommand=sub)

        assert result.subcommand is sub
        assert result.is_leaf is False
        assert result.has_subcommand is True

    def test_nested_subcommands(self):
        up = ParseResult(args=(), command="up")
        compose = ParseResult(args=(), command="compose", subcommand=up)
        docker = ParseResult(args=(), command="docker", subcommand=compose)

        assert docker.subcommand is compose
        assert compose.subcommand is up
        assert up.is_leaf is True


class TestParseResultPath:
    def test_path_for_single_command(self):
        result = ParseResult(args=(), command="git")

        assert result.path == ("git",)

    def test_path_for_command_with_subcommand(self):
        sub = ParseResult(args=(), command="commit")
        result = ParseResult(args=(), command="git", subcommand=sub)

        assert result.path == ("git", "commit")

    def test_path_for_deeply_nested_commands(self):
        up = ParseResult(args=(), command="up")
        compose = ParseResult(args=(), command="compose", subcommand=up)
        docker = ParseResult(args=(), command="docker", subcommand=compose)

        assert docker.path == ("docker", "compose", "up")


class TestParseResultIteration:
    def test_iter_yields_single_result(self):
        result = ParseResult(args=(), command="test")

        results = list(result)

        assert results == [result]

    def test_iter_yields_hierarchy_root_to_leaf(self):
        leaf = ParseResult(args=(), command="commit")
        root = ParseResult(args=(), command="git", subcommand=leaf)

        results = list(root)

        assert results == [root, leaf]

    def test_iter_yields_all_levels(self):
        up = ParseResult(args=(), command="up")
        compose = ParseResult(args=(), command="compose", subcommand=up)
        docker = ParseResult(args=(), command="docker", subcommand=compose)

        results = list(docker)

        assert [r.command for r in results] == ["docker", "compose", "up"]


class TestParseResultLength:
    def test_len_for_single_command(self):
        result = ParseResult(args=(), command="test")

        assert len(result) == 1

    def test_len_for_nested_commands(self):
        up = ParseResult(args=(), command="up")
        compose = ParseResult(args=(), command="compose", subcommand=up)
        docker = ParseResult(args=(), command="docker", subcommand=compose)

        assert len(docker) == 3


class TestParseResultDepth:
    def test_get_depth_for_leaf_command(self):
        result = ParseResult(args=(), command="test")

        assert result.get_depth() == 0

    def test_get_depth_with_one_subcommand(self):
        sub = ParseResult(args=(), command="commit")
        result = ParseResult(args=(), command="git", subcommand=sub)

        assert result.get_depth() == 1

    def test_get_depth_with_nested_subcommands(self):
        up = ParseResult(args=(), command="up")
        compose = ParseResult(args=(), command="compose", subcommand=up)
        docker = ParseResult(args=(), command="docker", subcommand=compose)

        assert docker.get_depth() == 2


class TestParseResultDeepestSubcommand:
    def test_get_deepest_returns_self_when_leaf(self):
        result = ParseResult(args=(), command="test")

        assert result.get_deepest_subcommand() is result

    def test_get_deepest_returns_leaf_subcommand(self):
        leaf = ParseResult(args=(), command="commit")
        root = ParseResult(args=(), command="git", subcommand=leaf)

        assert root.get_deepest_subcommand() is leaf

    def test_get_deepest_for_deep_hierarchy(self):
        up = ParseResult(args=(), command="up")
        compose = ParseResult(args=(), command="compose", subcommand=up)
        docker = ParseResult(args=(), command="docker", subcommand=compose)

        assert docker.get_deepest_subcommand() is up


class TestParseResultReversed:
    def test_reversed_for_single_command(self):
        result = ParseResult(args=(), command="test")

        results = list(result.reversed())

        assert results == [result]

    def test_reversed_yields_leaf_to_root(self):
        leaf = ParseResult(args=(), command="commit")
        root = ParseResult(args=(), command="git", subcommand=leaf)

        results = list(root.reversed())

        assert results == [leaf, root]

    def test_reversed_for_deep_hierarchy(self):
        up = ParseResult(args=(), command="up")
        compose = ParseResult(args=(), command="compose", subcommand=up)
        docker = ParseResult(args=(), command="docker", subcommand=compose)

        results = list(docker.reversed())

        assert [r.command for r in results] == ["up", "compose", "docker"]


class TestParseResultOptionAccess:
    def test_get_option_returns_value(self):
        result = ParseResult(args=(), command="test", options={"verbose": True})

        assert result.get_option("verbose") is True

    def test_get_option_returns_default_for_missing(self):
        result = ParseResult(args=(), command="test")

        assert result.get_option("verbose") is None
        assert result.get_option("verbose", False) is False

    def test_has_option_returns_true_when_present(self):
        result = ParseResult(args=(), command="test", options={"verbose": True})

        assert result.has_option("verbose") is True

    def test_has_option_returns_false_when_missing(self):
        result = ParseResult(args=(), command="test")

        assert result.has_option("verbose") is False


class TestParseResultPositionalAccess:
    def test_get_positional_returns_value(self):
        result = ParseResult(
            args=(),
            command="test",
            positionals={"files": ("a.txt", "b.txt")},
        )

        assert result.get_positional("files") == ("a.txt", "b.txt")

    def test_get_positional_returns_default_for_missing(self):
        result = ParseResult(args=(), command="test")

        assert result.get_positional("files") is None
        assert result.get_positional("files", ()) == ()

    def test_has_positional_returns_true_when_present(self):
        result = ParseResult(args=(), command="test", positionals={"files": ("a.txt",)})

        assert result.has_positional("files") is True

    def test_has_positional_returns_false_when_missing(self):
        result = ParseResult(args=(), command="test")

        assert result.has_positional("files") is False


class TestParseResultFindOption:
    def test_find_option_in_current_command(self):
        result = ParseResult(args=(), command="test", options={"verbose": True})

        assert result.find_option("verbose") is True

    def test_find_option_in_parent_command(self):
        leaf = ParseResult(args=(), command="commit")
        root = ParseResult(
            args=(), command="git", options={"verbose": True}, subcommand=leaf
        )

        assert root.find_option("verbose") is True

    def test_find_option_prefers_leaf_value(self):
        leaf = ParseResult(args=(), command="commit", options={"verbose": "leaf-value"})
        root = ParseResult(
            args=(), command="git", options={"verbose": "root-value"}, subcommand=leaf
        )

        # find_option searches leaf to root, returns first match
        assert root.find_option("verbose") == "leaf-value"

    def test_find_option_returns_none_when_missing(self):
        result = ParseResult(args=(), command="test")

        assert result.find_option("verbose") is None


class TestParseResultFindPositional:
    def test_find_positional_in_current_command(self):
        result = ParseResult(args=(), command="test", positionals={"files": ("a.txt",)})

        assert result.find_positional("files") == ("a.txt",)

    def test_find_positional_returns_none_when_missing(self):
        result = ParseResult(args=(), command="test")

        assert result.find_positional("files") is None


class TestParseResultGetAllOptions:
    def test_get_all_options_for_single_command(self):
        result = ParseResult(
            args=(), command="test", options={"verbose": True, "output": "file.txt"}
        )

        assert result.get_all_options() == {"verbose": True, "output": "file.txt"}

    def test_get_all_options_merges_hierarchy(self):
        leaf = ParseResult(args=(), command="commit", options={"message": "fix bug"})
        root = ParseResult(
            args=(), command="git", options={"verbose": True}, subcommand=leaf
        )

        merged = root.get_all_options()

        assert merged == {"verbose": True, "message": "fix bug"}

    def test_get_all_options_leaf_overrides_root(self):
        leaf = ParseResult(args=(), command="commit", options={"verbose": False})
        root = ParseResult(
            args=(), command="git", options={"verbose": True}, subcommand=leaf
        )

        merged = root.get_all_options()

        assert merged["verbose"] is False


class TestParseResultGetAllPositionals:
    def test_get_all_positionals_for_single_command(self):
        result = ParseResult(
            args=(), command="test", positionals={"files": ("a.txt", "b.txt")}
        )

        assert result.get_all_positionals() == {"files": ("a.txt", "b.txt")}

    def test_get_all_positionals_merges_hierarchy(self):
        leaf = ParseResult(args=(), command="add", positionals={"files": ("a.txt",)})
        root = ParseResult(
            args=(), command="git", positionals={"paths": ("/repo",)}, subcommand=leaf
        )

        merged = root.get_all_positionals()

        assert merged == {"paths": ("/repo",), "files": ("a.txt",)}


class TestParseResultRepr:
    def test_repr_minimal(self):
        result = ParseResult(args=(), command="test")

        assert "ParseResult(command='test')" in repr(result)

    def test_repr_includes_options_keys(self):
        result = ParseResult(args=(), command="test", options={"verbose": True})

        r = repr(result)
        assert "options=" in r

    def test_repr_includes_subcommand(self):
        sub = ParseResult(args=(), command="commit")
        result = ParseResult(args=(), command="git", subcommand=sub)

        r = repr(result)
        assert "subcommand='commit'" in r


class TestParseResultStr:
    def test_str_single_command(self):
        result = ParseResult(args=(), command="git")

        assert str(result) == "git"

    def test_str_command_hierarchy(self):
        sub = ParseResult(args=(), command="commit")
        result = ParseResult(args=(), command="git", subcommand=sub)

        assert str(result) == "git commit"


class TestParseResultToDict:
    def test_to_dict_minimal(self):
        result = ParseResult(args=("--verbose",), command="test")

        d = result.to_dict()

        assert d["command"] == "test"
        assert d["args"] == ("--verbose",)
        assert d["options"] == {}
        assert d["positionals"] == {}
        assert d["subcommand"] is None

    def test_to_dict_with_subcommand(self):
        sub = ParseResult(args=(), command="commit")
        result = ParseResult(args=(), command="git", subcommand=sub)

        d = result.to_dict()

        assert d["subcommand"] is not None
        assert d["subcommand"]["command"] == "commit"
