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

(流程不变, 使用阶段四的输出)

阶段六 (手动): GIS 数据集

(流程不变, (B) 部分任务)

阶段七 (StoryMaps): 最终整合

(流程不变, 整合所有输出)
