from mysql.api import DatabaseApi
import threading


def select():
    def _handle_one_thread(start_idx, end_idx):
        i = 0
        db_client = DatabaseApi()
        for idx in range(start_idx, end_idx):
            fid = factories[idx]
            i += 1
            f_file = db_client.find_contract_file_by_id(fid)
            f_relation_id = db_client.select_relation_id_by_factory_id(fid)[0]
            f_relation = db_client.find_contract_relation_by_id(f_relation_id)
            if len(f_file.create_date) > 0 and len(f_relation.create_type) > 0:
                db_client.save_date_type(f_file.create_date, f_relation.create_type)
                print(f_file.create_date, f_relation.create_type)
                print(i, part_size)

    client = DatabaseApi()
    factories = client.select_factories()
    thread_num = 8
    part_size = len(factories) // thread_num  # 向下取整，剩下的部分暂时忽略
    threads = []
    for i in range(8):
        start_idx = i * part_size
        end_idx = start_idx + part_size
        thread = threading.Thread(target=_handle_one_thread, args=(start_idx, end_idx))
        threads.append(thread)
        thread.start()
    end_thread = threading.Thread(target=_handle_one_thread,
                                  args=(thread_num * part_size, len(factories)))
    threads.append(end_thread)
    end_thread.start()
    # 等待所有线程执行结束
    for thread in threads:
        thread.join()
    print("Complete!!!")


if __name__ == '__main__':
    select()
