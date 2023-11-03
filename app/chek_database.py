import psycopg2
import os
import paramiko
import matplotlib.pyplot as plt
from prettytable import PrettyTable
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
        cursor.execute('''
            SELECT datname, usename, state
            FROM pg_stat_activity
            ORDER BY query_start DESC
            LIMIT 10
        ''')
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        
        headers = [desc[0] for desc in cursor.description]
        column_widths = [max(len(header), max(len(str(row[i])) for row in result)) for i, header in enumerate(headers)]

        table = "<code>"
        for i, header in enumerate(headers):
            table += f"<b>{header.ljust(column_widths[i])}</b> "
        table += "\n" + "-"*sum(column_widths) + "\n"

        for row in result:
            for i, value in enumerate(row):
                table += str(value).ljust(column_widths[i]) + " "
            table += "\n"

        table += "</code>"

        return table
    except psycopg2.Error as e:
        return None    

#############################################
#              check_info                   #
#############################################

async def get_system_info():
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

        return {
            'longest_transaction': longest_transaction_duration,
            'active_sessions': active_sessions,
            'sessions_lwlock': sessions_with_lwlock,
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



#############################################
#               settings                    #
#############################################

async def restart_postgresql():
    try:
        ssh_host = os.environ.get("DB_HOST")
        ssh_port = 22
        ssh_username = os.environ.get("SSH_USERNAME")
        ssh_password = os.environ.get("SSH_PASSWORD")

        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ssh_host, ssh_port, ssh_username, ssh_password)

        restart_command = "sudo service postgresql restart"

        stdin, stdout, stderr = ssh_client.exec_command(restart_command)
        exit_code = stdout.channel.recv_exit_status()

        ssh_client.close()

        if exit_code == 0:
            return True 
        else:
            return False #("Произошла ошибка при попытке перезапуска PostgreSQL на удаленном сервере.")
    except Exception as e:
       return None