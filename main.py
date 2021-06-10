import paramiko
import time
import os
from lxml import etree
from datetime import datetime
from xml.etree import ElementTree

folders = []
files_in = []
count = 0
stings_count = 0

config_file = 'config.xml'
if not os.path.exists(config_file):
    root_ = etree.Element('config')

    mainLine_ = etree.SubElement(root_, 'connect')
    line_ = etree.SubElement(mainLine_, 'address')
    line_.text = 'sftp_address'
    line_ = etree.SubElement(mainLine_, 'port')
    line_.text = '22'
    line_ = etree.SubElement(mainLine_, 'login')
    line_.text = 'login'
    line_ = etree.SubElement(mainLine_, 'password')
    line_.text = 'password'

    mainLine_ = etree.SubElement(root_, 'folders_server')
    line_ = etree.SubElement(mainLine_, 'f')
    line_.text = 'folder in sftp server'

    mainLine_ = etree.SubElement(root_, 'folder_in')
    line_ = etree.SubElement(mainLine_, 'f')
    line_.text = 'folder in local pc'

    mainLine_ = etree.SubElement(root_, 'other')
    line_ = etree.SubElement(mainLine_, 'delay')
    line_.text = 'delay between connections in seconds'

    xml_data = etree.tostring(root_, pretty_print=True, xml_declaration=True, encoding='utf-8').decode('utf-8')

    with open(config_file, 'w') as xml_config:
        xml_config.write(xml_data)
        quit(f'Отсутствует конфигурационный файл: {config_file}.\nСоздан новый файл, заполните конфигурационные данные в файле: {config_file}.')


def save_log(text):
    if not os.path.exists('LOG'):
        os.mkdir('LOG')
    try:
        file_name = datetime.now().strftime("LOG\%Y-%m-%d_history.log")
        log_file = open(file_name, 'a', encoding='utf-8')
        log_file.write(text)
        log_file.close()
    except PermissionError:
        print('Нет прав доступа к файлу логов "history.log"')
        print('Логирование не производится!!!')


with open(config_file) as f:
    doc = ElementTree.parse(f)
    data = doc.getroot()

    address = data.find('./connect/address').text
    port = int(data.find('./connect/port').text)
    login = data.find('./connect/login').text
    password = data.find('./connect/password').text
    delay = int(data.find('./other/delay').text)

    folder_in = str(data.find('./folder_in/f').text)

    for folders_list in data.findall('./folders_server/f'):
        folders.append(folders_list.text)

if not os.path.exists(folder_in.strip('/')):
    os.makedirs(folder_in.strip('/'))


def cls():
    global stings_count
    if stings_count > 200:
        stings_count = 0
        os.system('cls' if os.name == 'nt' else 'clear')
    else:
        stings_count += 1


while True:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(address, port=port, username=login, password=password)
        sftp = ssh.open_sftp()
    except Exception as exc:
        cls()
        print('\n* !!! Error in sftp connect: ' + exc.__class__.__name__ + datetime.now().strftime(" %H:%M:%S    %Y-%m-%d"))
        save_log('\n* !!! Error in sftp connect: ' + exc.__class__.__name__ + datetime.now().strftime(" %H:%M:%S    %Y-%m-%d") + '\n')
        time.sleep(delay)
        continue

    try:
        for folder in folders:
            files_local = os.listdir('.' + folder_in)  # Список файлов в локальной директории
            files_server = sftp.listdir(path=folder)  # Список файлов в директории на сервере
            files_in = list(set(files_server) - set(files_local))  # Поиск и исключение одинаковых (по имени) файлов

            if files_in:
                cls()
                save_log('\n# Скачивание файлов из папки: ' + folder + '\n')
                print('\n# Скачивание файлов из папки: ' + folder)
                for file in files_in:
                    sftp.get(folder + file, '.' + folder_in + file)
                    cls()
                    print(f'# {file}\t\t{datetime.now().strftime("%H:%M:%S    %Y-%m-%d")}')
                    save_log(f'# {file}\t\t{datetime.now().strftime("%H:%M:%S    %Y-%m-%d")}\n')
                    count = 0

            files_in.clear()
    except Exception as exc:
        cls()
        print('\n* !!! Ошибка при копировании файла: ' + str(exc) + ' # ' + datetime.now().strftime("%H:%M:%S    %Y-%m-%d"))
        save_log('\n* !!! Ошибка при копировании файла: ' + str(exc) + ' # ' + datetime.now().strftime("%H:%M:%S    %Y-%m-%d") + '\n')
        time.sleep(delay)

    ssh.close()

    if count == 60:
        print(f' = {count / (delay / 60)} мин.')
        save_log(f' = {count / (delay / 60)} мин.\n')
        count = 0
    print('*', end='')
    save_log('*')
    time.sleep(delay)
    count += 1
