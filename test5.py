from enum import Enum

class TestEnum(Enum):
    TEST1 = "test1"
    TEST2 = "test2"
    TEST3 = "test3"

print(TestEnum("test4") in [TestEnum.TEST1])
