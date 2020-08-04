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

def get_template(request):
    try: 
        file_loader = FileSystemLoader(r'UI')
        env = Environment(loader=file_loader)
        template = env.get_template('index.html')
        countries = ['ok', 'ok']
        output = template.render(countries=countries)

    except Exception as e:
        tb = sys.exc_info()[2]
        lineno = tb.tb_lineno
        print("Error in cgi server, reason: {}, line of error: {}".format(e, lineno))

    return output


def handle_client_request(request, request_headers, request_body):
    body = ''
    headers = ''
    path = request.split(' ')[1]
    ext = path.split('.')[-1]
    host = request_headers['Host']
    
    try: 
        if host == 'levysite.duckdns.org:8080':
            filename = ''
            if ext in content_types:
                if ext == 'json':
                    '''body = '''

                    headers = f"Cache-Control: private, max-age=3600\r\n"
                    commandline = f"HTTP/1.1 {HTTPStatus.OK.value} {HTTPStatus.OK.phrase}\r\n"
                    headers += f'Content-Length: {len(body)}\r\n'
                    headers += f"Content-Type: {ext}; charset=UTF-8\r\n\r\n"
                    return commandline.encode(), headers.encode(), body
                else:
                    filename = path

                with open(os.path.join(os.path.dirname(os.getcwd()), 'UI', filename.replace('/', '')), 'rb') as f:
                    body = f.read()

            elif '/' == path:
                ext = 'text/html'
                body = get_template(request).encode()

            commandline = f"HTTP/1.1 {HTTPStatus.OK.value} {HTTPStatus.OK.phrase}\r\n"
            headers += f'Content-Length: {len(body)}\r\n'
            headers += f"Content-Type: {ext}; charset=UTF-8\r\n\r\n"
            return commandline.encode(), headers.encode(), body
        
        else:
            ext = 'text/html'
            with open(os.path.join(os.path.dirname(os.getcwd()), 'secondProject-blog', 'UI', 'netalevysitedown.html'), 'rb') as f:
                body = f.read()
            commandline = f"HTTP/1.1 {HTTPStatus.OK.value} {HTTPStatus.OK.phrase}\r\n"
            headers += f'Content-Length: {len(body)}\r\n'
            headers += f"Content-Type: {ext}; charset=UTF-8\r\n\r\n"
            return commandline.encode(), headers.encode(), body

    except Exception as e:
        tb = sys.exc_info()[2]
        lineno = tb.tb_lineno
        print("Error in cgi server, reason: {}, line of error: {}".format(e, lineno))


def is_bad_ip(client_socket, addr):
    if addr[0] == '192.168.14.1' or addr[0] == '127.0.0.1':
        return False

    api_response = DbIpCity.get(addr[0], api_key='free')
    addr_country = api_response.country
    print("Country: " + addr_country)

    if addr_country == 'IL':
        return False

    with open(r'HTTP & CGI Servers\addresses.json') as json_file:  # default 'r' - read mode
        data_temp = json.load(json_file)
        for country in data_temp:
            if addr[0] in country:
                return True

    if addr_country != None:
        data_temp = ''
        with open(r'HTTP & CGI Servers\addresses.json') as json_file:  # default 'r' - read mode
            data_temp = json.load(json_file)
            if addr_country not in data_temp:
                data_temp[addr_country] = [addr[0]]
            else:
                country_addresses = data_temp[addr_country]
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
