import pandas as pd
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 启动浏览器
driver = webdriver.Edge()

# 定义要访问的URL
url = "https://www.shanghairanking.cn/rankings/bcur/2025"

try:
    # 访问目标URL
    driver.get(url)
    # 浏览器窗口最大化
    driver.maximize_window()

    # 显式等待表格加载完成
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, '//tbody/tr'))
    )

    # 等待额外时间确保数据加载
    time.sleep(3)

    # 创建空列表，用于存储爬取到的学校信息
    contents = []
    # 获取当前页面的完整HTML源代码
    html = driver.page_source
    # 将HTML字符串转换为lxml可解析的对象
    root = etree.HTML(html)
    # 使用XPath定位到表格中存放学校信息的所有<tr>节点
    school_info_list = root.xpath('//tbody/tr')

    # 遍历每个学校的信息节点
    for school_info in school_info_list:
        try:
            # 提取排名
            rank_data = school_info.xpath('./td[1]/div/text()')[0].strip() if school_info.xpath(
                './td[1]/div/text()') else ''

            # 提取学校名称 - 根据提供的HTML片段调整XPath
            name_data = school_info.xpath('.//span[@class="name-cn"]/text()')
            if name_data:
                name_data = name_data[0].strip()
            else:
                # 如果直接获取不到，尝试其他方式
                name_data = school_info.xpath('.//a[contains(@class, "name")]/text()')
                name_data = name_data[0].strip() if name_data else ''

                if not name_data:  # 如果还是获取不到，尝试从logo的alt属性获取
                    name_data = school_info.xpath('.//img[@class="univ-logo"]/@alt')
                    name_data = name_data[0].strip() if name_data else '未知学校'

            # 提取其他信息
            province_data = school_info.xpath('./td[3]/text()')[0].strip() if school_info.xpath(
                './td[3]/text()') else ''
            type_data = school_info.xpath('./td[4]/text()')[0].strip() if school_info.xpath('./td[4]/text()') else ''
            score_data = school_info.xpath('./td[5]/text()')[0].strip() if school_info.xpath('./td[5]/text()') else ''
            level_data = school_info.xpath('./td[6]/text()')[0].strip() if school_info.xpath('./td[6]/text()') else ''

            # 将提取的数据添加到contents中
            contents.append([rank_data, name_data, province_data, type_data, score_data, level_data])

        except Exception as e:
            print(f"Error processing a school: {e}")
            continue

    # 打印爬取到的原始数据列表
    print(f"Found {len(contents)} schools")
    for i, item in enumerate(contents[:5]):  # 打印前5条看看
        print(f"School {i + 1}: {item}")

    # 定义DataFrame的列名
    columns = ["排名", "学校名称", "省市", "类型", "总分", "办学层次"]
    # 将contents转换为DataFrame
    rank = pd.DataFrame(contents, columns=columns)

    # 尝试数据类型转换
    try:
        rank["排名"] = pd.to_numeric(rank["排名"], errors='coerce').fillna(0).astype(int)
        rank["总分"] = pd.to_numeric(rank["总分"], errors='coerce')
        rank["办学层次"] = pd.to_numeric(rank["办学层次"], errors='coerce')
    except Exception as e:
        print(f"Error converting data types: {e}")

    # 打印DataFrame的前几行
    print(rank.head())

    # 将处理好的数据保存为Excel文件
    rank.to_excel("2025中国大学排名.xlsx", index=False)
    print("保存成功！")

except Exception as e:
    print(f"An error occurred: {e}")
    # 如果出错，把HTML保存下来方便调试
    with open("debug_page.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("已保存当前页面HTML到debug_page.html")

finally:
    # 关闭浏览器，释放资源
    driver.quit()