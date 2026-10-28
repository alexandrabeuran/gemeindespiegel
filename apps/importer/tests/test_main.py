import pytest

from importer import main


def test_main_fails_until_the_import_exists() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main()
    assert exit_info.value.code != 0
