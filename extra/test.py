from typing import Union, List, Dict, Tuple


def function_with_weird_types(
    data: Union[List["str"], Dict, Tuple[str, int]]
) -> Union[int, float, str]:
    """
    @arg meme: test
    """
    return 1
