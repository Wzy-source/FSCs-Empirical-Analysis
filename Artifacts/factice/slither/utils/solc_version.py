import subprocess
import re


def get_target_solc_version(source_file):
    # 读取Solidity源代码文件并提取Solidity编译器版本号
    with open(source_file, "r") as file:
        source_code = file.read()
        """
        solidity版本号的表示方法：
        ① pragma solidity 0.8.0
        ② pragma solidity ^0.8.0
        ③ pragma solidity >=0.8.0
        ④ pragma solidity <=0.8.0
        ⑤ pragma solidity =0.8.10 >=0.8.10 >=0.8.0 <0.9.0
        ⑥ pragma solidity >=0.6.0 <0.8.0
        """
        pattern = r'pragma solidity\s*[>=^<]*\s*([0-9]+\.[0-9]+\.[0-9]+)'
        pragma_matches = re.findall(pattern, source_code)
        if pragma_matches:
            if len(pragma_matches) == 1:
                required_version = pragma_matches[0]
                print(f"所需的Solidity版本号是: {required_version}")
                return required_version
            else:
                print("错误匹配了多个版本号", pragma_matches)
        else:
            print("未找到Solidity编译器版本指令。请检查源代码文件中的pragma solidity指令。")
    return None


def set_solc_version(required_version):
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
