# -*- coding: utf-8 -*-
import arcpy
import os
import csv

arcpy.env.overwriteOutput = True

# 固定字段名
TYPE_FIELD = "遗迹类型"


def add_msg(msg):
    arcpy.AddMessage(str(msg))
    print(msg)


def count_feature_types(feature_fc, type_field):
    """
    统计图层中各遗迹类型数量
    返回 dict: {遗迹类型: 数量}
    """
    counts = {}
    with arcpy.da.SearchCursor(feature_fc, [type_field]) as cursor:
        for row in cursor:
            val = row[0]
            if val is None or str(val).strip() == "":
                val = "未分类"
            val = str(val).strip()
            counts[val] = counts.get(val, 0) + 1
    return counts


def write_csv(output_csv, rows, headers):
    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)


def main():
    # ==========================
    # 读取参数
    # ==========================
    feature_a = arcpy.GetParameterAsText(0)   # 发掘区A遗迹
    feature_b = arcpy.GetParameterAsText(1)   # 发掘区B遗迹
    output_folder = arcpy.GetParameterAsText(2)  # 输出文件夹

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    add_msg("开始执行发掘区域遗迹组合结构对比分析...")

    # ==========================
    # 检查字段是否存在
    # ==========================
    fields_a = [f.name for f in arcpy.ListFields(feature_a)]
    fields_b = [f.name for f in arcpy.ListFields(feature_b)]

    if TYPE_FIELD not in fields_a:
        raise ValueError("发掘区A图层中不存在字段：{}".format(TYPE_FIELD))
    if TYPE_FIELD not in fields_b:
        raise ValueError("发掘区B图层中不存在字段：{}".format(TYPE_FIELD))

    # ==========================
    # 统计 A、B 区遗迹类型数量
    # ==========================
    add_msg("统计发掘区A遗迹类型数量...")
    counts_a = count_feature_types(feature_a, TYPE_FIELD)

    add_msg("统计发掘区B遗迹类型数量...")
    counts_b = count_feature_types(feature_b, TYPE_FIELD)

    total_a = sum(counts_a.values())
    total_b = sum(counts_b.values())

    if total_a == 0:
        raise ValueError("发掘区A输入图层中没有要素。")
    if total_b == 0:
        raise ValueError("发掘区B输入图层中没有要素。")

    # ==========================
    # 合并统计结果
    # ==========================
    all_types = sorted(set(counts_a.keys()) | set(counts_b.keys()))

    rows = []
    for t in all_types:
        a_count = counts_a.get(t, 0)
        b_count = counts_b.get(t, 0)

        a_ratio = round(a_count / float(total_a) * 100, 2) if total_a > 0 else 0
        b_ratio = round(b_count / float(total_b) * 100, 2) if total_b > 0 else 0

        rows.append([t, a_count, a_ratio, b_count, b_ratio])

    # 加总计行
    rows.append(["总计", total_a, 100.0, total_b, 100.0])

    # ==========================
    # 输出 CSV
    # ==========================
    output_csv = os.path.join(output_folder, "发掘区域遗迹组合结构对比表.csv")
    headers = ["遗迹类型", "发掘区A数量", "发掘区A比例(%)", "发掘区B数量", "发掘区B比例(%)"]
    write_csv(output_csv, rows, headers)

    add_msg("对比表已输出：{}".format(output_csv))

    # ==========================
    # 可选：输出 ArcGIS 表
    # ==========================
    output_table = os.path.join(output_folder, "发掘区域遗迹组合结构对比表.dbf")
    if arcpy.Exists(output_table):
        arcpy.management.Delete(output_table)

    arcpy.management.CreateTable(output_folder, "发掘区域遗迹组合结构对比表.dbf")
    arcpy.management.AddField(output_table, "遗迹类型", "TEXT", field_length=50)
    arcpy.management.AddField(output_table, "A_数量", "LONG")
    arcpy.management.AddField(output_table, "A_比例", "DOUBLE")
    arcpy.management.AddField(output_table, "B_数量", "LONG")
    arcpy.management.AddField(output_table, "B_比例", "DOUBLE")

    with arcpy.da.InsertCursor(output_table, ["遗迹类型", "A_数量", "A_比例", "B_数量", "B_比例"]) as cursor:
        for r in rows:
            cursor.insertRow(r)

    add_msg("ArcGIS表已输出：{}".format(output_table))
    add_msg("工具运行完成。")


if __name__ == "__main__":
    main()