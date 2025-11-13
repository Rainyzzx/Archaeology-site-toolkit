import arcpy
import math
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
import os

import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
matplotlib.rcParams['axes.unicode_minus'] = False   # 解决负号显示为方块

def calculate_angle(polygon):
    array = polygon.getPart(0)
    if len(array) < 2:
        return None
    p1 = array[0]
    p2 = array[1]
    dx = p2.X - p1.X
    dy = p2.Y - p1.Y
    angle = math.degrees(math.atan2(dy, dx))
    return (angle + 360) % 360

def bin_direction(angle):
    dirs = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
    idx = int(((angle + 22.5) % 360) / 45)
    return dirs[idx]

def main():
    input_fc = arcpy.GetParameterAsText(0)  # 输入图层
    temp_selected = "in_memory/selected"
    temp_mbg = "in_memory/mbg"

    # 只筛选 type = 'M' 的记录
    arcpy.Select_analysis(input_fc, temp_selected, "\"type\" = 'M'")

    # 如果没有选中要素，直接退出
    count = int(arcpy.GetCount_management(temp_selected)[0])
    if count == 0:
        arcpy.AddMessage("未找到 type = 'M' 的墓葬数据。")
        return

    # 生成最小外接矩形
    arcpy.MinimumBoundingGeometry_management(temp_selected, temp_mbg, "RECTANGLE_BY_WIDTH")

    counts = defaultdict(int)
    with arcpy.da.SearchCursor(temp_mbg, ["SHAPE@"]) as cursor:
        for row in cursor:
            polygon = row[0]
            angle = calculate_angle(polygon)
            if angle is None:
                continue
            direction = bin_direction(angle)
            counts[direction] += 1

    # 开始画图
    directions = ['北', '东北', '东', '东南', '南', '西南', '西', '西北']
    angles = np.linspace(0, 2 * np.pi, len(directions), endpoint=False).tolist()
    angles += angles[:1]
    values = [counts.get(d, 0) for d in directions]
    values += values[:1]

    plt.figure(figsize=(6, 6))
    ax = plt.subplot(111, polar=True)
    ax.plot(angles, values, marker='o', label="墓葬")
    ax.fill(angles, values, alpha=0.25)
    ax.set_thetagrids(np.degrees(angles[:-1]), directions)
    ax.set_title("墓葬朝向分布图", fontsize=14)
    ax.legend(loc='upper right')
    plt.tight_layout()
    plt.show()

    arcpy.AddMessage("图像已显示。")

if __name__ == "__main__":
    main()
