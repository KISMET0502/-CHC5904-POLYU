# -CHC5904-POLYU
计划总览：四阶段法
阶段一 (Python - 脚本 1): 情感分析
任务： 修复 OpenCC 错误，读取繁体 CSV，转换为简体，运行情感分析。
输出： sentiment_per_chapter.png
阶段二 (Python - 脚本 2): 自动人物发现 (新！)
任务： 使用 jieba 的词性标注功能，从繁体文本中自动提取所有被标记为“人名”(nr)的词语。
输出： potential_characters_freq.csv (一个包含大量潜在人物和“噪音”的列表)
阶段三 (手动校对): 人物白名单 (新！)
任务： 你（研究者） 必须打开 potential_characters_freq.csv，手动清理它，删除所有“噪音”（如地名、官职、普通词汇），只保留真实的人物名称。
输出： CHARACTER_WHITELIST.txt (你项目的权威人物名单)
阶段四 (Python - 脚本 3): 网络数据准备
任务： 读取你手动清理过的 CHARACTER_WHITELIST.txt，然后运行与之前相同的共现分析。
输出： fengshen_nodes.csv 和 fengshen_edges.csv (用于 Gephi)
阶段五 (Gephi): 网络可视化
上述均已完成

需要做的
阶段六 (手动): GIS 数据集
(B) GIS 事件数据库 (手动创建)
目标： 这是你的“B部分”（GIS）的核心，你需要手动创建一个包含地理信息的事件列表。
打开 Excel (或 Google Sheets)。
创建新表格，并包含以下英文表头 (使用英文表头能确保 StoryMaps 100% 兼容)：
Chapter (章节)
Event_Name (事件名称, 如: 哪吒鬧海)
Location_Name (地点名称, 如: 陳塘關)
Event_Type (事件类型, 如: 戰爭 / 法寶)
Characters (涉及人物, 如: 哪吒, 敖丙)
Latitude (纬度, 如: 39.084)
Longitude (经度, 如: 117.761)
Quote (引文, 从 out/fengshen_paragraphs.csv 中复制关键原文)
填充数据：
打开你抓取的 out/fengshen_paragraphs.csv 作为参考。
开始阅读并填充你的 Excel 表格。
查找坐标： 使用在线地图工具（如谷歌地图）查找“朝歌”（河南安阳）、“西岐”（陕西岐山）等真实地点的经纬度。对于虚构地点（如“陈塘关”），根据书中的描述（例如“靠近东海”）给它一个合理的坐标。
保存文件：
将你的 Excel 表格另存为 fengshen_events.csv (确保编码为 UTF-8)。
阶段七 (StoryMaps): 最终整合
