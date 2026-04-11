"""国家肖像 portraits/TAG.txt."""
import os


def write_country_portraits(tag, output_dir):
    """生成 portraits/<TAG>.txt — HOI4 顶级 portraits 目录

    【崩溃根因】HOI4 在启动游戏时为每个国家自动生成缺失的 scientist，
    它从 portraits/<TAG>.txt 或 portraits/continent_xxx.txt 里的 scientist 池
    随机选择肖像。如果国家没有这个文件，自动生成失败 → 崩溃。

    文件必须放在 MOD 根目录下的 portraits/ 文件夹（不是 common/portraits）。
    """
    d = os.path.join(output_dir, "portraits")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{tag}.txt"), "w", encoding="utf-8") as f:
        f.write(f"{tag} = {{\n")

        # scientist（关键，否则崩溃）
        f.write("\tscientist = {\n")
        f.write("\t\tmale = {\n")
        for i in range(1, 17):
            f.write(f'\t\t\t"GFX_portrait_generic_europe_male_{i:02d}"\n')
        f.write("\t\t}\n")
        f.write("\t\tfemale = {\n")
        for i in range(1, 17):
            f.write(f'\t\t\t"GFX_portrait_generic_europe_female_{i:02d}"\n')
        f.write("\t\t}\n")
        f.write("\t}\n")

        # army（将领）
        f.write("\tarmy = {\n")
        f.write("\t\tmale = {\n")
        for i in range(1, 6):
            f.write(f'\t\t\t"GFX_Portrait_Europe_Generic_land_{i}"\n')
        f.write("\t\t}\n")
        f.write("\t}\n")

        # navy（海军）
        f.write("\tnavy = {\n")
        f.write("\t\tmale = {\n")
        for i in range(1, 4):
            f.write(f'\t\t\t"GFX_Portrait_Europe_Generic_navy_{i}"\n')
        f.write("\t\t}\n")
        f.write("\t}\n")

        # political（领袖，按意识形态）
        f.write("\tpolitical = {\n")
        for i, ideo in enumerate(["communism", "democratic", "fascism", "neutrality"], 1):
            f.write(f"\t\t{ideo} = {{\n")
            f.write("\t\t\tmale = {\n")
            f.write(f'\t\t\t\t"GFX_Portrait_Europe_Generic_{i}"\n')
            f.write("\t\t\t}\n")
            f.write("\t\t}\n")
        f.write("\t}\n")

        # operative（特工）
        f.write("\toperative = {\n")
        f.write("\t\tmale = { \"GFX_portrait_operative_unknown\" }\n")
        f.write("\t\tfemale = { \"GFX_portrait_operative_unknown\" }\n")
        f.write("\t}\n")

        # fallback male/female
        f.write("\tmale = { \"GFX_portrait_unknown\" }\n")
        f.write("\tfemale = { \"GFX_portrait_unknown_female\" }\n")

        f.write("}\n")

