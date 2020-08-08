import os
import json
from ip2geotools.databases.noncommercial import DbIpCity
from jinja2 import Environment, FileSystemLoader
import requests
import logging
import time
import sqlite3
import sys
import hashlib
from http import HTTPStatus

content_types = {
        'html': 'text/html',
        'jpeg': 'image/jpeg',
        'jpg': 'image/jpeg',
        'png': 'image/png',
        'ico': 'image/ico',
        'gif': 'image/gif',
        'js': 'application/javascript; charset=UTF-8',
        'json': 'application/json',
        'css': 'text/css'
    }


def which_database(request, request_headers, request_body):
    database = ''
    if 'POST' in request:
        if '/login' in request or '/signup' in request:
            database = 'db_users'
        
        if '/card' in request:
            database = 'db_cards'

    elif 'GET' in request:
        if '/' in request:
            database = 'db_cards'

    return database
            

def insert_into_database(request, request_headers, request_body, database):
    conn = sqlite3.connect(r'DAL\\' + database + '.sqlite3')

    c = conn.cursor()
    if database == 'db_users':
        credentials = request_body.split('&')
        credentials_new = []
        i = 0
        for credential in credentials:
            credentials_new.append(credential.split('=')[1])
            i += 1

        c.execute(f'''CREATE TABLE IF NOT EXISTS {database}
            (uname TEXT PRIMARY KEY, psw TEXT, email TEXT)''')

        c.execute(
            f"INSERT INTO {database}(uname, psw, email) VALUES ('{credentials_new[0]}', '{credentials_new[1]}', '{credentials_new[2]}')")
    elif database == 'db_cards': 
        card_info = request_body.split('&')
        card_info_new = []
        
        i = 0
        for title in card_info:
            card_info_new.append(title.split('=')[1])
            i += 1

        
        c.execute(f'''CREATE TABLE IF NOT EXISTS {database}
            (title TEXT PRIMARY KEY, desc TEXT)''')

        c.execute(
            f"INSERT INTO {database}(title, desc) VALUES ('{card_info_new[0]}', '{card_info_new[1]}')")
    conn.commit()
    conn.close()


def get_from_database(request, request_headers, request_body, database):
    database = which_database(request, request_headers, request_body)

    conn = sqlite3.connect(r'DAL\\' + database + '.sqlite3')
    c = conn.cursor()

    if database == 'db_users':
        if '/login' in request:
            credentials = request_body.split('&')
            credentials_new = []
            for credential in credentials:
                i = 0
                credentials_new.append(credentials[i].split('=')[1])
                i += 1

            c.execute(f'''CREATE TABLE IF NOT EXISTS {database}
                (uname TEXT PRIMARY KEY, psw TEXT, email TEXT)''')

            c.execute(
                f"SELECT uname, psw, email FROM {database}")
            temp = c.fetchall()
            print(temp)
    elif database == 'db_cards':
        c.execute(f'''CREATE TABLE IF NOT EXISTS {database}
            (title TEXT PRIMARY KEY, desc TEXT)''')

        c.execute(
                f"SELECT title, desc FROM {database}")
        temp = c.fetchall()
        conn.commit()
        conn.close()

        return temp

def get_template(request, request_headers, request_body):
    try:
        file_loader=FileSystemLoader(r'UI')
        env=Environment(loader=file_loader)
        template=env.get_template('index.html')

        Response = ''
        cards = []

        database = which_database(request, request_headers, request_body)
        if 'GET' in request:
            if '/' in request:
                cards = get_from_database(request, request_headers, request_body, database)
                
        elif 'POST' in request:
            try:
                request_body = request_body.replace('+', ' ')
                insert_into_database(request, request_headers, request_body, database)
                cards = get_from_database(request, request_headers, request_body, database)
                Response = 'Post has been posted'

            except Exception as e:
                print_error(e)
                Response = 'Error has occured'
            
        output=template.render(cards=reversed(cards), Response=Response)
        return output

    except Exception as e:
        print_error(e)
        

def handle_client_request(request, request_headers, request_body):
    body=''
    headers=''
    path=request.split(' ')[1]
    try:
        ext=path.split('.')[-1]
    except:
        pass
    host=request_headers['Host']

    try:
        if host == '':
            if 'GET' in request:
                if ext in content_types:
                    with open(f'UI{path}' , 'rb') as f:
                        body = f.read()

                elif '/' == path:
                    ext='text/html'
                    body=get_template(request, request_headers,
                                    request_body).encode()

                commandline=f"HTTP/1.1 {HTTPStatus.OK.value} {HTTPStatus.OK.phrase}\r\n"
                headers += f'Content-Length: {len(body)}\r\n'
                headers += f"Content-Type: {ext}; charset=UTF-8\r\n\r\n"
                return commandline.encode(), headers.encode(), body

            elif 'POST' in request:

                ext='text/html'
                body=get_template(request, request_headers,
                                request_body).encode()

                commandline=f"HTTP/1.1 {HTTPStatus.OK.value} {HTTPStatus.OK.phrase}\r\n"
                headers += f'Content-Length: {len(body)}\r\n'
                headers += f"Content-Type: {ext}; charset=UTF-8\r\n\r\n"
                return commandline.encode(), headers.encode(), body


        else:
            ext='text/html'
            with open(os.path.join(os.path.dirname(os.getcwd()), 'secondProject-blog', 'UI', 'sitedown.html'), 'rb') as f:
                body=f.read()
            commandline=f"HTTP/1.1 {HTTPStatus.OK.value} {HTTPStatus.OK.phrase}\r\n"
            headers += f'Content-Length: {len(body)}\r\n'
            headers += f"Content-Type: {ext}; charset=UTF-8\r\n\r\n"
            return commandline.encode(), headers.encode(), body

    except Exception as e:
        print_error(e)



def is_bad_ip(client_socket, addr):
    if addr[0] == '' or addr[0] == '':
        return False

    api_response=DbIpCity.get(addr[0], api_key='free')
    addr_country=api_response.country
    print("Country: " + addr_country)

    if addr_country == 'IL':
        return False

    with open(r'HTTP & CGI Servers\addresses.json') as json_file:  # default 'r' - read mode
        data_temp=json.load(json_file)
        for country in data_temp:
            if addr[0] in country:
                return True

    if addr_country != None:
        data_temp=''
        with open(r'HTTP & CGI Servers\addresses.json') as json_file:  # default 'r' - read mode
            data_temp=json.load(json_file)
            if addr_country not in data_temp:
                data_temp[addr_country]=[addr[0]]
            else:
                country_addresses=data_temp[addr_country]
                if addr[0] in country_addresses:
                    print('Bad IP')
                    return True
                else:
                    country_addresses.append(addr[0])

        write_json(data_temp)
        print('Bad IP')
        return True


def write_json(data, filename='addresses.json'):
    with open(r'HTTP & CGI Servers\addresses.json', 'w') as f:
        json.dump(data, f, indent=4)

def print_error(exception):
    tb=sys.exc_info()[2]
    lineno=tb.tb_lineno
    print("Error in cgi server, reason: {}, line of error: {}".format(exception, lineno))
