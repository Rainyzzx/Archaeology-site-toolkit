# -*- coding: utf-8 -*-
import arcpy
import os
from arcpy.sa import *

arcpy.env.overwriteOutput = True
arcpy.CheckOutExtension("Spatial")

# 读取输入参数
site_points = arcpy.GetParameterAsText(0)   # 遗址点
river_fc = arcpy.GetParameterAsText(1)      # 河流
dem = arcpy.GetParameterAsText(2)           # DEM
study_area = arcpy.GetParameterAsText(3)    # 研究区

# 权重（写死）
weight_elev = 0.3
weight_slope = 0.3
weight_water = 0.4

# 输出目录
workspace = arcpy.env.scratchFolder
if not workspace:
    workspace = arcpy.env.workspace

arcpy.env.workspace = workspace

arcpy.AddMessage("开始遗址分布预测分析...")

# ------------------------------
# Step 1 提取遗址环境因子
# ------------------------------

arcpy.AddMessage("提取遗址环境因子")

# 高程
elev_values = ExtractValuesToPoints(site_points, dem,
                                    os.path.join(workspace, "site_elev"))

# 坡度
slope = Slope(dem)
slope_values = ExtractValuesToPoints(site_points, slope,
                                     os.path.join(workspace, "site_slope"))

# 河流距离
river_dist = EucDistance(river_fc)
river_values = ExtractValuesToPoints(site_points, river_dist,
                                     os.path.join(workspace, "site_dist"))

# ------------------------------
# Step 2 获取适宜范围
# ------------------------------

def get_range(fc, field):
    values = []
    with arcpy.da.SearchCursor(fc, field) as cursor:
        for row in cursor:
            if row[0] is not None:
                values.append(row[0])
    values.sort()
    low = values[int(len(values)*0.25)]
    high = values[int(len(values)*0.75)]
    return low, high

elev_low, elev_high = get_range(elev_values, "RASTERVALU")
slope_low, slope_high = get_range(slope_values, "RASTERVALU")
dist_low, dist_high = get_range(river_values, "RASTERVALU")

arcpy.AddMessage("环境范围计算完成")

# ------------------------------
# Step 3 栅格标准化
# ------------------------------

arcpy.AddMessage("计算环境适宜度")

elev_score = Con((Raster(dem) >= elev_low) & (Raster(dem) <= elev_high), 1, 0)
slope_score = Con((Raster(slope) >= slope_low) & (Raster(slope) <= slope_high), 1, 0)
dist_score = Con((Raster(river_dist) >= dist_low) & (Raster(river_dist) <= dist_high), 1, 0)

# ------------------------------
# Step 4 权重叠加
# ------------------------------

suitability = (elev_score * weight_elev +
               slope_score * weight_slope +
               dist_score * weight_water)

suitability_raster = os.path.join(workspace, "site_suitability.tif")
suitability.save(suitability_raster)

arcpy.AddMessage("适宜性栅格生成完成")

# ------------------------------
# Step 5 高潜力区提取
# ------------------------------

high_potential = Con(suitability >= 0.6, 1)

high_raster = os.path.join(workspace, "high_potential.tif")
high_potential.save(high_raster)

high_polygon = os.path.join(workspace, "high_potential_area.shp")

arcpy.RasterToPolygon_conversion(high_potential, high_polygon, "SIMPLIFY")

arcpy.AddMessage("高潜力区提取完成")

arcpy.AddMessage("工具运行完成")
arcpy.AddMessage("适宜性栅格: " + suitability_raster)
arcpy.AddMessage("潜在遗址区: " + high_polygon)