"""descriptor.mod 写入."""
import os
from data.constants import (
    DEFAULT_MOD_VERSION, DEFAULT_SUPPORTED_VERSION, REPLACE_PATHS,
)


def write_descriptor(mod_name, output_dir):
    rp = "\n".join(f'replace_path="{p}"' for p in REPLACE_PATHS)

    # 内部 descriptor.mod（MOD目录内）
    with open(os.path.join(output_dir, "descriptor.mod"), "w") as f:
        f.write(f'version="{DEFAULT_MOD_VERSION}"\n')
        f.write('tags={\n\t"Alternative History"\n\t"Map"\n\t"Total Conversion"\n}\n')
        f.write(f'name="{mod_name}"\n')
        f.write(f'supported_version="{DEFAULT_SUPPORTED_VERSION}"\n')
        f.write(rp + "\n")

    # 外层 .mod 文件（MOD目录旁边，启动器需要）
    mod_dir_name = os.path.basename(output_dir)
    outer_mod = os.path.join(os.path.dirname(output_dir), f"{mod_dir_name}.mod")
    with open(outer_mod, "w") as f:
        f.write(f'version="{DEFAULT_MOD_VERSION}"\n')
        f.write('tags={\n\t"Alternative History"\n\t"Map"\n\t"Total Conversion"\n}\n')
        f.write(f'name="{mod_name}"\n')
        f.write(f'supported_version="{DEFAULT_SUPPORTED_VERSION}"\n')
        # path 用正斜杠
        abs_path = os.path.abspath(output_dir).replace("\\", "/")
        f.write(f'path="{abs_path}"\n')
        f.write(rp + "\n")

