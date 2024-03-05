# 智能合约用法分类工具集
import json
from json import JSONDecodeError
from typing import Dict
from mysql.api import ContractFile, DatabaseApi


def find_main_contract_code_by_id(contract_id: int) -> str:
    """
    给定合约id，返回主合约源码
    """
    contract_file: ContractFile = DatabaseApi().find_contract_file_by_id(contract_id)
    source_code = contract_file.source_code
    contract_name = contract_file.name

    try:
        # etherscan might return an object with two curly braces, {{ content }}
        dict_source_code = json.loads(source_code[1:-1])
        return _handle_standard_json_input(dict_source_code, contract_name)

    except JSONDecodeError:
        try:
            # or etherscan might return an object with single curly braces, { content }
            dict_source_code = json.loads(source_code)
            return _handle_standard_json_input(dict_source_code, contract_name)

        except JSONDecodeError:  # 无依赖合约形式
            return source_code


def _handle_standard_json_input(sj: Dict, name: str) -> str:
    if "sources" in sj:
        # etherscan可能会返回一个带有sources属性的对象，包含所有合约的源码
        sources = sj["sources"]
    else:
        # or etherscan可能会返回以合约名称为key的对象
        sources = sj
    for file_path, file, in sources.items():
        if name == file_path.split('/')[-1].split('.')[0]:
            return file['content']

def get_all_relations():
    #获取表construct_relation内所有pair
    return DatabaseApi().get_all_contract_relations()

if __name__ == '__main__':
    result=get_all_relations()
    print(result[:10],len(result))
