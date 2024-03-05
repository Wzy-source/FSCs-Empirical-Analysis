import json

from mysql.api import DatabaseApi, ContractFile
import re
import subprocess
import os
from api_config import api_keys
import random

# 数据库原始数据集，在遍历的过程中，可能会加入一些后续请求得到的数据集
total_contract_num = 327681
start_id = 0


def preprocess_contracts(start):
    """
    合约预处理
    依次从数据库中取合约名、编译器版本、源码字符串，保存为临时文件
    设置本地编译器版本
    调用slither进行分析
    直到分析到数据库中最后一个合约为止
    """
    # 统计数据
    traversed_num = start
    db_client = DatabaseApi()
    # 获取数据库首个合约文件
    contract = db_client.traversal_contract_file(start)
    while contract is not None:
        traversed_num += 1
        # 编译前预检查，排除一定不是工厂的可能性，减少因为编译造成的时间消耗
        if not must_not_factory(contract.name, contract.source_code):
            # 设置本地编译器版本,有些版本号可能以"v"开头，将v去除
            print(
                f"contract name:{contract.name} id:{contract.id} address:{contract.address} 合约可能是factory合约，进行预处理")
            # set_solc_version(contract.compiler)
            # 保存一个.sol临时文件到$HOME环境变量下
            # 有些合约是后来保存的，可能是未被验证的合约，没有源代码
            if contract.name and contract.source_code and contract.address:
                project_path = os.path.join(os.environ['HOME'], 'tempcode')
                # target_file_name = f"{contract.chain}-{contract.address}-{contract.name}.sol"
                # target_file_path = save_temp_project(project_path, target_file_name, contract.source_code)
                # 调用slither的scf_preprocessor组件
                try:
                    call_scf_preprocessor(contract.address, project_path)
                except Exception as e:
                    print(f"执行detector:scf_preprocessor时出错{e}")
                # 删除file_path下的文件
                delete_temp_project(project_path)
        # 遍历下一个文件
        contract = db_client.traversal_contract_file(contract.id)
        # 更新新的start_id,用于程序崩溃时重新在数据库中start的位置
        global start_id
        start_id = contract.id
        print(f"preprocess_contracts start_id更新为{start_id}")

        traverse_percentage = "{:.2f}%".format((traversed_num / total_contract_num) * 100)
        print(
            f"已遍历合约:{traversed_num},遍历进度约为:{traverse_percentage}")
    print("Contracts Preprocess Complete!")


def call_scf_preprocessor(address, project_path):
    # 随机选取API_KEY,防止达到请求次数上限
    random_key = api_keys[random.randint(0, len(api_keys) - 1)]
    python_env_path = os.path.join(os.getcwd(), "..", "env/bin/python")
    command = f"{python_env_path} -m slither {address}" \
              f" --etherscan-export-directory {project_path}" \
              f" --etherscan-apikey {random_key}" \
              f" --detect scf-preprocessor"
    print(command)
    subprocess.run(command, shell=True, check=True)


def set_solc_version(required_version):
    required_version = required_version.split("+")[0].replace("v", "")
    # commands
    install_command = f"solc-select install {required_version}"
    use_command = f"solc-select use {required_version}"
    # local installed versions
    versions_output = subprocess.check_output(["solc-select", "versions"]).decode("utf-8")
    installed_versions = re.findall(r"\d+\.\d+\.\d+", versions_output)
    # 如果目标版本的solc没有下载，需下载后再指定该版本
    if required_version not in installed_versions:
        print(f"Solidity {required_version} 未在本地下载，需先下载")
        subprocess.run(install_command, shell=True, check=True)
        print(f"Solidity {required_version} 已成功下载")
    subprocess.run(use_command, shell=True, check=True)
    print(f"成功切换到 Solidity {required_version}")


def save_temp_project(project_path, target_file_name, source_code) -> str:
    """
    两种情况：
    1.source_code为源码形式
    2.source_code为standard_json形式
    """
    if not source_code.startswith("{{"):
        return save_sol_code_to_file(source_code, project_path, target_file_name)
    else:
        return save_standard_json_to_project(source_code, project_path, target_file_name)


def save_sol_code_to_file(source_code, project_path, target_file_name):
    file_path = os.path.join(project_path, target_file_name)
    try:
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        with open(file_path, "w") as file:
            file.write(source_code)
            print(f'文件已成功保存到 {file_path}')
    except Exception as e:
        print(f'保存文件时发生错误：{e}')
    return file_path


"""
将standard_json保存为可编译的project形式
"""


def save_standard_json_to_project(source_code, project_path, target_file_name):
    info: dict = json.loads(source_code[1:-1])
    language, sources, settings = info['language'], info['sources'], info['settings']
    target_file_path = ""
    if language == 'Solidity':
        # 遍历sources
        for file_path, file, in sources.items():
            code: str = file['content']
            # 将code中的import路径按照remappings规则逆向映射
            # S1：提取code中所有import语句
            import_pattern = r"(import\s+.*?\n\s*\{[^}]*\}\s*from\s*\"[^\"]*\";)|(import\s+.*?;)"
            import_statements = re.finditer(import_pattern, code, flags=re.DOTALL)
            for import_statement in import_statements:
                # 找到匹配单引号或者双引号的路径
                path_pattern = r'["\'](.*?)["\']'
                import_path: str = re.findall(path_pattern, import_statement.group(0), flags=re.DOTALL)[0]
                if not import_path.startswith("."):
                    # S2：找到匹配当前import的remappings rule
                    matched_prefix, target = "", ""
                    if 'remappings' in settings:
                        matched_remapping_rule = find_matched_remapping_rule(import_path, settings['remappings'])
                        if matched_remapping_rule:
                            cp_t = matched_remapping_rule.split("=")
                            matched_prefix, target = cp_t[0], cp_t[1]
                    # S3：加入绝对路径，然后将remappings rule应用并替换import path
                    new_import_path = os.path.join(project_path, import_path).replace(matched_prefix, target)
                    code = code.replace(import_statement.group(0),
                                        import_statement.group(0).replace(import_path, new_import_path))

            # S4:将处理过的code保存到文件夹中
            # 如果是目标代码文件（非依赖），则将文件名设置为target_file_name形式
            # target_file_name："{chain}-{address}-{name}.sol"
            target_contract_name = target_file_name.split("-")[2]
            if target_contract_name == file_path.split("/")[-1]:
                file_path = file_path.replace(target_contract_name, target_file_name)
                target_file_path = os.path.join(project_path, file_path)

            abs_file_path = os.path.join(project_path, file_path)
            folder_path = os.path.dirname(abs_file_path)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
            with open(abs_file_path, "w") as f:
                f.write(code)

        return target_file_path


def find_matched_remapping_rule(path: str, remappings: list) -> str:
    matched_rule, longest_prefix = "", ""
    for rule in remappings:
        # Import remappings have the form of context:prefix=target
        cp_t = rule.split("=")
        prefix, target = cp_t[0], cp_t[1]
        if path.startswith(prefix) and len(prefix) >= len(longest_prefix):
            longest_prefix = prefix
            matched_rule = rule
    return matched_rule


def delete_temp_project(project_path):
    remove_command = f"rm -rf {project_path}"
    try:
        subprocess.run(remove_command, shell=True, check=True)
        print(f'临时项目 {project_path} 已成功删除')
    except Exception as e:
        print(f'删除文件时发生错误：{e}')


# 基于源码字符串层次的分析
# 1.正则匹配，检查合约字符串中是否存在内联汇编create/create2关键字
# 2.检查是否有new ContractName关键字
def must_not_factory(name, source_code: str) -> bool:
    def must_not_factory_contract(contract_names: list, target_code: str) -> bool:
        create_pattern = r'assembly\s*{[^}]*\b(create|create2)\b[^}]*}'
        create_matches = re.findall(create_pattern, target_code, re.DOTALL)
        if create_matches:
            return False
        for cn in contract_names:
            new_contract_statement = f"new {cn}"
            if new_contract_statement in target_code:
                return False
        return True

    if source_code:
        # 获取所有代码中出现的智能合约的合约名
        maybe_contract_names = []
        new_contract_pattern = r'contract\s+([^\s{]+)\s*{'
        new_contract_matches = re.findall(new_contract_pattern, source_code, re.DOTALL)
        for match in new_contract_matches:
            maybe_contract_names.append(match)
        if source_code.startswith("{{"):
            # standard_json形式:只看main contract
            info: dict = json.loads(source_code[1:-1])
            language, sources = info['language'], info['sources']
            if language == 'Solidity':
                for file_path, file, in sources.items():
                    contract_name = file_path.replace('.sol', '').split("/")[-1]
                    if contract_name == name:  # main contract
                        return must_not_factory_contract(maybe_contract_names, file['content'])
            return True
        else:  # 无依赖合约形式
            return must_not_factory_contract(maybe_contract_names, source_code)
    else:
        return True


if __name__ == "__main__":
    preprocess_contracts(start_id)

"""
✅contract name:Ret_rn id:226 合约可能是factory合约，进行预处理
更新关于"new"字段的预判断
✅Source "@openzeppelin/contracts/access/Ownable.sol" not found: File not found.：使用了绝对路径
✅删除文件时发生错误：[Errno 1] Operation not permitted: '/Users/mac/tempcode'：使用了rm -rf指令
✅Error: Stack too deep. Try compiling with `--via-ir` (cli) or the equivalent `viaIR: true` (standard JSON) while enabling the optimizer
✅Error: Source "/Users/mac/tempcode/src/interfaces/ICreatorRoyaltiesControl.sol" not found: File outside of allowed directories.
  在env/lib/python3.8/site-packages/crytic_compile/platform/solc.py的allow-path中加入了"/Users/mac/tempcode"
"""
