import arcpy
import matplotlib.pyplot as plt
import matplotlib
import os

def ScriptTool(site_layer, river_layer):
    arcpy.env.overwriteOutput = True

    arcpy.AddMessage("Running Near analysis...")
    arcpy.analysis.Near(site_layer, river_layer)
    arcpy.AddMessage("Near analysis completed.")

    # 添加分类字段
    tag_field = "相关性"
    if tag_field not in [f.name for f in arcpy.ListFields(site_layer)]:
        arcpy.AddField_management(site_layer, tag_field, "TEXT")

    # 分类赋值
    with arcpy.da.UpdateCursor(site_layer, ["NEAR_DIST", tag_field]) as cursor:
        for row in cursor:
            dist = row[0]
            if dist != -1 and dist <= 10000:
                row[1] = "相关"
            else:
                row[1] = "不相关"
            cursor.updateRow(row)

    arcpy.AddMessage("Classification complete.")

    # 统计数量
    stats = {"相关": 0, "不相关": 0}
    with arcpy.da.SearchCursor(site_layer, [tag_field]) as cursor:
        for row in cursor:
            if row[0] in stats:
                stats[row[0]] += 1

    # 绘制柱状图
    matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 黑体
    matplotlib.rcParams['axes.unicode_minus'] = False  # 正常显示负号

    labels = list(stats.keys())
    values = [stats[l] for l in labels]
    x = range(len(labels))

    plt.figure(figsize=(6, 4))
    plt.bar(x, values, color=["green", "gray"])
    plt.xticks(x, labels)
    plt.title("近水性分布遗址数量")
    plt.ylabel("数量")
    for i, v in enumerate(values):
        plt.text(i, v + 0.5, str(v), ha='center')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    site_layer = arcpy.GetParameterAsText(0)
    river_layer = arcpy.GetParameterAsText(1)
    ScriptTool(site_layer, river_layer)
