__version__ = "0.0.1"
import base64
import io
import os.path
import time
from collections.abc import Iterable
from os import PathLike

import matplotlib.pyplot as plt
import requests
from PIL import Image


class Mermaid2ImageError(Exception):
    pass


class Mermaid2Image:
    # https://mermaid.js.org/config/theming.html#available-themes
    THEMES = ["default", "neutral", "dark", "forest", "base"]
    SUPPORTED_FILES = [".md"]

    def __init__(
        self,
        mmd_input: str | bytes | PathLike[str] | PathLike[bytes] | Iterable | None = None,
        image_path: str | None = None,
        theme: str | None = None,
        courtesy_sleep: int = 1,
    ):
        """Mermaid markdown to image.
        mmd_input can be:
        - a mermaid markdown string
        - a `.md` file containing mermaid code block/s
        - iterable of all of the above

        theme priority:
        - from_src > from_code

        :param mmd_input: mermaid markdown input
        :param image_path: path of the output image
        :param theme: theme to apply to output diagram/s
        :param courtesy_sleep: sleep time between mermaid API calls (enforced to min 1s)
        """
        self.mmd_input = mmd_input
        self.image_name = image_path
        self.theme = theme
        self._courtesy_sleep = None
        self.courtesy_sleep = courtesy_sleep

        self.__mermaid_ink_url = "https://mermaid.ink/img/"

    @property
    def courtesy_sleep(self):
        return self._courtesy_sleep

    @courtesy_sleep.setter
    def courtesy_sleep(self, c_sleep):
        self._courtesy_sleep = c_sleep if c_sleep > 1 else 1

    def __generate(self, mmd_str: str) -> None:
        """Generate image file from given mmd string.

        :param mmd_str: mermaid markdown string.
        """
        if self.theme is not None and not self.__has_theme_set(mmd_str):
            mmd_str = self.__add_theme(mmd_str)
        graph_bytes = mmd_str.encode("utf8")
        base64_bytes = base64.urlsafe_b64encode(graph_bytes)
        base64_string = base64_bytes.decode("ascii")
        returned_image_data = requests.get(
            self.__mermaid_ink_url + base64_string
        ).content
        img = Image.open(io.BytesIO(returned_image_data))
        # img.save('mermaid.png')
        plt.imshow(img)
        plt.show()
        time.sleep(self.courtesy_sleep)

    def __add_theme(self, mmd_str: str) -> str:
        """Add theme to the mermaid string.

        :param mmd_str: mermaid string without the theme
        :return: mermaid string with theme added
        """
        if self.theme is not None and self.theme not in self.THEMES:
            raise ValueError(f"Theme '{self.theme}' is not supported.")

        theme = f"%%{{init: {{'theme':'{self.theme}'}}}}%%\n"
        return theme + mmd_str

    @staticmethod
    def __has_theme_set(mmd_str: str) -> bool:
        """Does mermaid string have theme defined?

        :param mmd_str: mermaid string
        """
        return "init:" in mmd_str and "'theme':" in mmd_str

    def generate(
        self,
        mmd_input: str | bytes | PathLike[str] | PathLike[bytes] | Iterable,
        image_name: str | None = None,
        theme: str | None = None,
    ) -> None:
        """Generate image file from given mermaid markdown input.
        Input can be:
        - a mermaid markdown string
        - a `.md` file containing mermaid code block/s
        - iterable of all of the above

        :param mmd_input: mermaid markdown input
        :param theme: theme to apply to output diagram/s
        """
        if theme is not None:
            self.theme = theme
        if isinstance(mmd_input, list | tuple | set):
            print("mmd is collection (list, tuple, set)")
            for mmd_str in mmd_input:
                self.generate(mmd_str, theme=theme)
        elif os.path.isfile(mmd_input):
            print("mmd is file")
            path = mmd_input
            self.__generate_from_file(path)
        elif isinstance(mmd_input, str):
            print("mmd is string")
            self.__generate(mmd_input)
        else:
            raise TypeError(f"mmd is of invalid type '{type(mmd)}'")

    def __generate_from_file(
        self, path: str | bytes | PathLike[str] | PathLike[bytes]
    ) -> None:
        """Find mermaid markdown in file and generate diagram/s from it.

        :param path: path to file containing mermaid code block/s
        :param theme: theme to apply to output diagram/s
        """
        if os.path.splitext(path)[1] not in self.SUPPORTED_FILES:
            raise ValueError(
                f"File type '{os.path.splitext(path)[1]}' is not supported."
            )

        with open(path, "r") as mmd_file:
            mmd_str_lines = mmd_file.readlines()

        found_mmd_strings = []
        find_op = "find_start"
        for line_i, line in enumerate(mmd_str_lines):
            match find_op:
                case "find_start":
                    if line.strip().startswith("```mermaid"):
                        line_start_i = line_i
                        next_op = "find_end"
                    else:
                        continue
                case "find_end":
                    if line.strip().startswith("```"):
                        line_end_i = line_i
                        next_op = "find_start"
                        found_mmd_strings.append(
                            "".join(mmd_str_lines[line_start_i + 1 : line_end_i])
                        )
                    else:
                        continue
                case _:
                    raise Mermaid2ImageError(
                        f"next_op <'{find_op}'> could not do that, ...??"
                    )
            find_op = next_op
        self.generate(found_mmd_strings)


if __name__ == "__main__":
    m2i = Mermaid2Image(courtesy_sleep=0.5)
    print(m2i.courtesy_sleep)
    m2i.courtesy_sleep = 5
    print(m2i.courtesy_sleep)

    mmd = """
    graph LR;
        A--> B & C & D;
        B--> A & E;
        C--> A & E;
        D--> A & E;
        E--> B & C & D;
    """

    # m2i.generate(mmd, theme="forest")
    # m2i.generate("test_mmd.md")
    m2i.generate(["test_mmd.md", mmd], theme="dark")
