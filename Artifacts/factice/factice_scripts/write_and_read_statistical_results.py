from mysql.api import DatabaseApi
import json
import os


def write_create_date_total_contract_count_by_type(contract_type):
    db_client = DatabaseApi()
    date_count_list = db_client.find_create_date_total_contract_count_by_type(contract_type=contract_type)
    temp = 0
    for i in range(len(date_count_list)):
        temp += date_count_list[i][1]
        date_count_list[i][1] = temp
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "statistics", f"create_date_total_contract_count_{contract_type}" + '.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(date_count_list, json_file)


def write_factory_num_percent_and_txcount():
    db_client = DatabaseApi()
    factory_num_and_txcount = db_client.find_factory_num_and_txcont()
    total_factory_num = 0
    for row in factory_num_and_txcount:
        total_factory_num += row[0]
    cumulative_prob = []
    front_num = 0
    X = []
    for row in factory_num_and_txcount:
        front_num += row[0]
        cumulative_prob.append(front_num/total_factory_num)
        X.append(row[1])
    factory_num_percent_and_txcount = [X, cumulative_prob]
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "statistics", f"factory_num_percent_and_txcount" + '.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(factory_num_percent_and_txcount, json_file)


def write_contract_percent_and_execute_time():
    db_client = DatabaseApi()
    contract_execute_time = db_client.find_contract_execute_time()
    total_contract_num = 0
    timeout = 15
    for row in contract_execute_time:
        if row[0]/1e9 < timeout:
            total_contract_num += row[1]
    cumulative_prob = []
    front_num = 0
    execute_time = []
    for row in contract_execute_time:
        if row[0]/1e9 < timeout:
            front_num += row[1]
            cumulative_prob.append(front_num / total_contract_num)
            execute_time.append(row[0]/1e9)
    contract_percent_and_execute_time = [execute_time, cumulative_prob]
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "statistics", f"contract_percent_and_execute_time" + '.json')
    with open(json_file_path, 'w') as json_file:
        json.dump(contract_percent_and_execute_time, json_file)


def get_contract_num_by_chain_and_type(chain, contract_type):
    """按照network分别统计factory & created的总数"""
    db_client = DatabaseApi()
    return len(db_client.find_by_contract_chain_and_type(chain, contract_type))


def read_create_date_total_contract_count_by_type(contract_type):
    """获取factory & created & normal三种合约的数量随时间的变化/以Day为单位"""
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "statistics", f"create_date_total_contract_count_{contract_type}" + '.json')
    with open(json_file_path, 'r') as json_file:
        return json.load(json_file)


def read_factory_num_percent_and_txcount():
    """获取百分之多少的factory执行了多少次以下的交易"""
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "statistics", f"factory_num_percent_and_txcount" + '.json')
    with open(json_file_path, 'r') as json_file:
        return json.load(json_file)


def read_contract_percent_and_execute_time():
    """获取百分比合约执行时间"""
    json_file_path = os.path.join(os.path.dirname(__file__), "..", "statistics", f"contract_percent_and_execute_time" + '.json')
    with open(json_file_path, 'r') as json_file:
        return json.load(json_file)


if __name__ == '__main__':
    contract_types = ['factory', 'created', 'normal']
    for contract_type in contract_types:
        write_create_date_total_contract_count_by_type(contract_type)
    write_factory_num_percent_and_txcount()
    write_contract_percent_and_execute_time()