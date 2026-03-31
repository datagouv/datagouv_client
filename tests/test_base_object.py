import pytest

from datagouv.base_object import BaseObject


def test_not_instanciable():
    with pytest.raises(TypeError):
        BaseObject("a")
