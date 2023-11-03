import psycopg2
import os
#import paramiko
import matplotlib.pyplot as plt
from datetime import datetime
import io
from dotenv import load_dotenv
load_dotenv()


#############################################
#              check_activity               #
#############################################
async def get_database_activity():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DP_PORT"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD")
        )
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pg_stat_activity')
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    except psycopg2.Error as e:
        return None    

#############################################
#              check_info                   #
#############################################


# async def check_disk_and_cpu_use():
#     ssh_client = paramiko.SSHClient()
#     ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     ssh_client.connect(
#         os.environ.get(""), 
#         username=os.environ.get(""),
#         password=os.environ.get(""))
    
#     command = "df -h"
#     stdin, stdout, stderr = ssh_client.exec_command(command)

#     output = stdout.read().decode('utf-8')
#     print('#########################')
#     print(output)
#     print('#########################')
#     ssh_client.close()
#     return output


async def get_database_and_system_info():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("DB_HOST"),
            port=os.environ.get("DP_PORT"),
            database=os.environ.get("DB_NAME"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD")
        )
        cursor = conn.cursor()

        # самая долгая транзакция
        cursor.execute('SELECT max(now() - xact_start) FROM pg_stat_activity')
        longest_transaction_duration = cursor.fetchone()[0]

        # количество активных сессий
        cursor.execute('SELECT count(*) FROM pg_stat_activity')
        active_sessions = cursor.fetchone()[0]

        # количество LWLock
        cursor.execute('SELECT count(*) FROM pg_stat_activity WHERE wait_event IS NOT NULL')
        sessions_with_lwlock = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        # места на диске
        #free_disk_space = await check_disk_and_cpu_use()

        # # загруженность
        # cpu_usage = psutil.cpu_percent(interval=1)

        return {
            'longest_transaction': longest_transaction_duration,
            'active_sessions': active_sessions,
            'sessions_lwlock': sessions_with_lwlock,
            #'free_disk': free_disk_space,
            #'cpu_use': cpu_usage
        }
    except psycopg2.Error as e:
        return None
    

async def send_photo(chat_id, x_keys, y):
    plt.figure(figsize=(8, 6))
    plt.title("Параметры")
    y[0] = y[0].total_seconds()
    data = [int(i) for i in y]
    plt.bar(x_keys, data)
    plt.ylabel('Значение')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    from main import bot
    await bot.send_photo(chat_id, photo=buf)