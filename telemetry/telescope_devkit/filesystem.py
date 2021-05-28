import os


def get_repo_path() -> str:
    path = os.path.realpath(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "./../../")
    )
    # print(path)
    return path
