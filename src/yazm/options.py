from dataclasses import dataclass


@dataclass
class Options:
    save_dir: str
    save_name: str
    log_instructions: bool
    rand_seed: bytearray | list
    highlight_objects: bool = True

    @classmethod
    def default(cls):
        return cls(save_dir="", save_name="", log_instructions=False, rand_seed=bytearray([90, 111, 114, 107]))
