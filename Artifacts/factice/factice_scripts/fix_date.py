import json
from datetime import datetime, timedelta
from factice_scripts.write_and_read_statistical_results import read_create_date_total_contract_count_by_type
import os


def uniform_date(datas, head_date, tail_date):
    """"填补日期空缺"""
    length = len(datas)
    id = 0
    new_datas = []
    while head_date <= tail_date:
        if id < length and head_date == datetime.strptime(datas[id][0], '%m/%d/%Y'):
            contract_count = datas[id][1]
            id += 1
            # '3/02/2021', '3/2/2021'会被显示成不同的一天
            while id < length and head_date == datetime.strptime(datas[id][0], '%m/%d/%Y'):
                contract_count = datas[id][1]
                id += 1
        else:
            if id == 0:
                contract_count = 0
            else:
                contract_count = datas[id - 1][1]
        new_datas.append([datetime.strftime(head_date, '%m/%d/%Y'), contract_count])
        head_date += timedelta(days=1)
    return new_datas


def write_to_file(contract_type, new_datas):
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "statistics",
                                  f"create_date_total_contract_count_{contract_type}" + '.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(new_datas, json_file)


def fix_date():
    """"对factory created normal合约数日期进行统一"""
    datas_created = read_create_date_total_contract_count_by_type('created')
    datas_factory = read_create_date_total_contract_count_by_type('factory')
    datas_normal = read_create_date_total_contract_count_by_type('normal')

    head_date = min(datetime.strptime(datas_created[0][0], '%m/%d/%Y'),
                    datetime.strptime(datas_factory[0][0], '%m/%d/%Y'),
                    datetime.strptime(datas_normal[0][0], '%m/%d/%Y'))

    tail_date = max(datetime.strptime(datas_created[-1][0], '%m/%d/%Y'),
                    datetime.strptime(datas_factory[-1][0], '%m/%d/%Y'),
                    datetime.strptime(datas_normal[-1][0], '%m/%d/%Y'))

    datas_created = uniform_date(datas_created, head_date, tail_date)
    datas_factory = uniform_date(datas_factory, head_date, tail_date)
    datas_normal = uniform_date(datas_normal, head_date, tail_date)

    write_to_file('created', datas_created)
    write_to_file('factory', datas_factory)
    write_to_file('normal', datas_normal)


if __name__ == '__main__':
    fix_date()