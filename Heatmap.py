import arcpy
from arcpy import env
from arcpy.sa import *
import os

# 启用 Spatial 分析模块
arcpy.CheckOutExtension("Spatial")
arcpy.env.overwriteOutput = True

# --- 用户输入参数 ---
input_polygon = arcpy.GetParameterAsText(0)  # 只需输入面状图层

# --- 自动设置 ---
workspace = arcpy.env.scratchGDB  # 使用临时数据库
basename = os.path.basename(input_polygon).split('.')[0]

output_point = os.path.join(workspace, f"{basename}_point")
output_raster = os.path.join(workspace, f"{basename}_heatmap")
search_radius = "2"  # 默认热力半径（单位：地图单位，建议根据你的投影是米）
# --- 面转点 ---
arcpy.AddMessage("正在将面要素转为质心点...")
arcpy.FeatureToPoint_management(input_polygon, output_point, "INSIDE")

# --- 生成热力图 ---
arcpy.AddMessage("正在生成热力图...")
heatmap = KernelDensity(output_point, None, search_radius)
heatmap.save(output_raster)

# --- 输出结果提示 ---
arcpy.AddMessage(f"热力图生成成功 ✅：{output_raster}")
arcpy.SetParameterAsText(1, output_raster)  # 若你在Toolbox中添加了输出参数