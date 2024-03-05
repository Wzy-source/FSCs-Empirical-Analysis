import matplotlib.pyplot as plt
import matplotlib.dates as mdate
import pandas as pd
from matplotlib.ticker import FuncFormatter
import numpy as np

from factice_scripts.write_and_read_statistical_results import read_create_date_total_contract_count_by_type, \
    read_factory_num_percent_and_txcount, read_contract_percent_and_execute_time


def plt_contract_count_by_create_date():
    datas_created = read_create_date_total_contract_count_by_type('created')
    datas_factory = read_create_date_total_contract_count_by_type('factory')
    datas_normal = read_create_date_total_contract_count_by_type('normal')
    dates = pd.date_range(start='2015-08-08', end='2023-11-19', freq='D')
    values_factory = []
    values_created = []
    values_normal = []
    for data in datas_factory:
        values_factory.append(data[1])
    for data in datas_created:
        values_created.append(data[1])
    for data in datas_normal:
        values_normal.append(data[1])

    # 绘制时间图
    fig = plt.figure(figsize=(12, 8))
    ax = plt.subplot(111)
    ax.xaxis.set_major_formatter(mdate.DateFormatter('%m/%d/%Y'))
    plt.xticks(pd.date_range(dates[0], dates[-1], 25), rotation=45)
    ax.plot(dates, values_factory, color='blue', label='factory')
    ax.plot(dates, values_created, color='green', label='created')
    ax.plot(dates, values_normal, color='darkorange', label='normal')
    # 设置 x y 轴名称
    ax.set_xlabel('date', fontsize=15)
    ax.set_ylabel('contract count', fontsize=15)
    plt.legend(loc="best", prop={'size': 15})
    plt.savefig('../statistics/contract_count.png', dpi=300)


def plt_CDF_of_factory_contract_txcount():
    factory_num_percent_and_txcount = read_factory_num_percent_and_txcount()
    X = factory_num_percent_and_txcount[0]
    cumulative_prob = factory_num_percent_and_txcount[1]
    # 绘制 CDF 图
    plt.plot(X[1:], cumulative_prob[1:], label='CDF')
    plt.xlabel('Txcount')
    # 设置 x 轴为对数轴
    plt.xscale('log')
    plt.ylabel('Percentage')
    plt.title('CDF_of_factory_contract_txcount')
    plt.savefig('../statistics/CDF_of_factory_contract_txcount', dpi=300)


def plt_CDF_of_contract_percent_and_execute_time():
    contract_percent_and_execute_time = read_contract_percent_and_execute_time()
    execute_time = contract_percent_and_execute_time[0]
    cumulative_prob = contract_percent_and_execute_time[1]
    # 绘制 CDF 图
    plt.plot(execute_time, cumulative_prob, label='CDF')
    plt.xlabel('Time(sec)')
    plt.ylabel('Percentage')
    plt.title('CDF of Contract Percent and Execute Time')
    plt.savefig('../statistics/CDF_of_contract_percent_and_execute_time', dpi=300)


# 自定义纵坐标刻度标签的格式
def format_millions(value, _):
    if value == 0:
        return 0
    return f'{value / 1e6} M'


def to_percent(y, position):
    """将y值转换为百分比字符串"""
    if y == 0:
        return 0
    return f"{100 * y:.0f}%"


def plt_contract_count_create_by_factory():
    """"绘制基于合约工厂创建的合约累计数量图(以月为单位)"""
    with open('../contract_data/contract_num_created_by_factory.txt', 'r') as file:
        lines = file.readlines()
        dates = []
        total_create_num = []
        for i in range(int(len(lines) / 2)):
            index = i * 2
            dates.append(lines[index].strip().split(sep=' ')[0])
            if i == 0:
                total_create_num.append(int(lines[index + 1]))
            else:
                total_create_num.append(int(lines[index + 1]) + total_create_num[i - 1])

    dates = pd.date_range(start=dates[0], end=dates[-1], freq='MS')
    # 绘制时间图
    plt.figure(figsize=(15, 6))
    ax = plt.subplot(111)
    ax.xaxis.set_major_formatter(mdate.DateFormatter('%Y-%m'))
    ax.yaxis.set_major_formatter(FuncFormatter(format_millions))
    plt.xticks(pd.date_range(dates[0], dates[-1], 15))
    ax.plot(dates, total_create_num)
    # 设置 x y 轴名称
    ax.set_xlabel('Year-Month', fontsize=15, fontweight='bold')
    ax.set_ylabel('Contract Count', fontsize=13, fontweight='bold')
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.savefig('../statistics/contract_count_create_by_factory.png', dpi=300)


quarters = ['2017-Q1', '2017-Q2', '2017-Q3', '2017-Q4',
            '2018-Q1', '2018-Q2', '2018-Q3', '2018-Q4',
            '2019-Q1', '2019-Q2', '2019-Q3', '2019-Q4',
            '2020-Q1', '2020-Q2', '2020-Q3', '2020-Q4',
            '2021-Q1', '2021-Q2', '2021-Q3', '2021-Q4',
            '2022-Q1', '2022-Q2', '2022-Q3', '2022-Q4',
            '2023-Q1', '2023-Q2', '2023-Q3']
quarters = [quarter[2:] for quarter in quarters]


def plt_factory_contracts():
    """绘制工厂合约数量、create2所占比例、low-level比例"""
    # 获取工厂合约数量
    with open('../contract_data/Factory Contract Quantity.txt', 'r') as file:
        lines = file.readlines()
        dates_factory_contract_quantity = []
        for i in range(int(len(lines) / 2)):
            index = i * 2
            date = lines[index].strip().split(sep=' ')[0]
            if '2017-01-01' <= date <= '2023-09-01':
                temp = int(lines[index + 1])
                dates_factory_contract_quantity.append([date, temp])
    dates_factory_contract_quantity = sorted(dates_factory_contract_quantity, key=lambda x: x[0])
    factory_contract_quantity = [row[1] for row in dates_factory_contract_quantity]

    # 获取create2所占比例
    df = pd.read_excel('../contract_data/create vs create2.xls', header=None)
    df = df.iloc[:, 1:3]
    create2_and_create = df.values
    create2_and_create = np.insert(create2_and_create, 26, [0, 0], axis=0)

    # 获取low-level所占比例
    df = pd.read_excel('../contract_data/low-level vs high-level.xlsx', header=None)
    df = df.iloc[:, 1:3]
    low_level_and_high_level = df.values
    # 填补空白月份
    low_level_and_high_level = np.insert(low_level_and_high_level, 26, [0, 0], axis=0)
    factory_contract_quantity_quarter = []
    create2_percent = []
    low_level_percent = []
    for i in range(int(len(factory_contract_quantity) / 3)):
        index = 3 * i
        temp1 = sum(factory_contract_quantity[index:index + 3])
        factory_contract_quantity_quarter.append(temp1)
        temp2 = np.sum(create2_and_create[index:index + 3, 0]) / np.sum(create2_and_create[index:index + 3, ])
        create2_percent.append(temp2)
        temp3 = np.sum(low_level_and_high_level[index:index + 3, 0]) / np.sum(
            low_level_and_high_level[index:index + 3, ])
        low_level_percent.append(temp3)

    plt.rcParams.update({'font.family': 'Times New Roman',  # 设置字体
                         'font.size': 12,  # 设置字体大小为12
                         })
    # 绘制柱状图
    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax1.bar(quarters, factory_contract_quantity_quarter, color='#70ADFF', edgecolor='black',
            label='# factory contract quantity')
    ax1.set_xlabel('Quarter')
    ax1.set_ylabel('# factory contracts')
    ax1.set_ylim(0, 12000)
    ax1.tick_params(axis='y')

    # ticks = range(len(quarters))
    # ax1.set_xticks(ticks)  # 设置刻度位置
    # ax1.set_xticklabels(quarters, rotation=45, ha="center")

    # 每隔一个刻度显示
    ticks = range(0, len(quarters), 2)
    ax1.set_xticks(ticks)
    ax1.set_xticklabels(quarters[::2], rotation=45, ha="center")
    # 增加y轴格线
    ax1.yaxis.grid(True, linestyle='-', linewidth=0.5, color='gray')

    # 在同一个图上绘制占比折线图
    ax2 = ax1.twinx()
    # 设置y轴的格式器为百分比
    formatter = FuncFormatter(to_percent)
    ax2.yaxis.set_major_formatter(formatter)
    ax2.plot(quarters, create2_percent, color='red', label='% create2', marker='o', markersize=3)
    ax2.plot(quarters, low_level_percent, color='#FF881D', label='% low-level', marker='o', markersize=3)
    ax2.set_ylabel('% factory contracts')
    ax2.set_ylim(bottom=0)
    ax2.set_yticks([0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9])
    ax2.tick_params(axis='y')

    # 去掉所有刻度线
    ax1.set_frame_on(False)
    ax1.tick_params(bottom=False, top=False, left=False, right=False)
    ax2.set_frame_on(False)
    ax2.tick_params(bottom=False, top=False, left=False, right=False)

    # 获取图例句柄和标签
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    # 合并图例句柄和标签
    handles = handles1 + handles2
    labels = labels1 + labels2

    # 创建统一的图例
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.21, 1.01))
    fig.tight_layout()  # 调整整体空白
    plt.savefig('../statistics/factory_contracts.pdf', dpi=300)


def plt_eoa_deploy_vs_factory_deploy():
    """绘制外部和工厂合约部署数量"""
    # 获取外部和工厂合约部署数量
    with open('../contract_data/EOA_DEPLOY vs FACTORY_DEPLOY_COUNT.txt', 'r') as file:
        lines = file.readlines()
        dates_eoa_deploy_and_factory_deploy = []
        for i in range(int(len(lines) / 3)):
            index = i * 3
            date = lines[index].strip().split(sep=' ')[0]
            dates_eoa_deploy_and_factory_deploy.append([date, int(lines[index + 1]), int(lines[index + 2])])
    dates_eoa_deploy_and_factory_deploy = sorted(dates_eoa_deploy_and_factory_deploy, key=lambda x: x[0])

    quarters = ['2016-Q1', '2016-Q2', '2016-Q3', '2016-Q4',
                '2017-Q1', '2017-Q2', '2017-Q3', '2017-Q4',
                '2018-Q1', '2018-Q2', '2018-Q3', '2018-Q4',
                '2019-Q1', '2019-Q2', '2019-Q3', '2019-Q4',
                '2020-Q1', '2020-Q2', '2020-Q3', '2020-Q4',
                '2021-Q1', '2021-Q2', '2021-Q3', '2021-Q4',
                '2022-Q1', '2022-Q2', '2022-Q3', '2022-Q4',
                '2023-Q1', '2023-Q2', '2023-Q3']
    quarters = [quarter[2:] for quarter in quarters]
    eoa_deploy_by_quarter = []
    factory_deploy_by_quarter = []
    factory_deploy_percent = []
    for i in range(int(len(dates_eoa_deploy_and_factory_deploy) / 3)):
        index = 3*i
        temp = dates_eoa_deploy_and_factory_deploy[index:index+3]
        eoa_deploy = 0
        factory_deploy = 0
        for row in temp:
            eoa_deploy += row[1]
            factory_deploy += row[2]
        eoa_deploy_by_quarter.append(eoa_deploy)
        factory_deploy_by_quarter.append(factory_deploy)
        factory_deploy_percent.append(factory_deploy/(eoa_deploy+factory_deploy))

    plt.rcParams.update({'font.family': 'Times New Roman',  # 设置字体
                         'font.size': 12,  # 设置字体大小为12
                         })

    # 绘制柱状图
    fig, ax1 = plt.subplots(figsize=(10, 5))
    bar_width = 0.4
    index = np.arange(len(quarters))
    ax1.bar(index, factory_deploy_by_quarter, bar_width, color='#70ADFF', edgecolor='black', label='# factory-deploy')
    ax1.bar(index + bar_width, eoa_deploy_by_quarter, bar_width, color='#FF881D', edgecolor='black',
            label='# eoa-deploy')
    ax1.set_xlabel('Quarter')
    ax1.set_ylabel('# contracts')
    ax1.set_ylim(bottom=0)
    step1 = 0.6e6
    ax1.set_yticks([i * step1 for i in range(11)])
    ax1.yaxis.set_major_formatter(FuncFormatter(format_millions))
    ax1.tick_params(axis='y')
    # ticks = range(len(quarters))
    # ax1.set_xticks(ticks)  # 设置刻度位置
    # ax1.set_xticklabels(quarters, rotation=45, ha="center")

    # 每隔一个取一个
    ticks = range(0, len(quarters), 2)
    ax1.set_xticks(ticks)
    ax1.set_xticklabels(quarters[::2], rotation=45, ha="center")
    # 增加y轴格线
    ax1.yaxis.grid(True, linestyle='-', linewidth=0.5, color='gray')

    # 在同一个图上绘制占比折线图
    ax2 = ax1.twinx()
    # 设置y轴的格式器为百分比
    formatter = FuncFormatter(to_percent)
    ax2.yaxis.set_major_formatter(formatter)
    ax2.plot(quarters, factory_deploy_percent, color='red', label='% factory-deploy', marker='o', markersize=3)
    ax2.set_ylabel('% contracts')
    ax2.set_ylim(bottom=0)
    step2 = 0.1
    ax2.set_yticks([i*step2 for i in range(11)])
    ax2.tick_params(axis='y')

    ax1.set_frame_on(False)
    ax1.tick_params(bottom=False, top=False, left=False, right=False)
    ax2.set_frame_on(False)
    ax2.tick_params(bottom=False, top=False, left=False, right=False)

    # 获取图例句柄和标签
    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()

    # 合并图例句柄和标签
    handles = handles1 + handles2
    labels = labels1 + labels2

    # 创建统一的图例
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.18, 1))

    fig.tight_layout()  # 调整整体空白
    plt.savefig('../statistics/factory_vs_eao.pdf', dpi=300)


if __name__ == '__main__':
    # plt_contract_count_by_create_date()
    # plt_CDF_of_factory_contract_txcount()
    # plt_CDF_of_contract_percent_and_execute_time()
    # plt_contract_count_create_by_factory()
    plt_factory_contracts()
    plt_eoa_deploy_vs_factory_deploy()
