import socket
import threading
from datetime import datetime
import sys
from http import HTTPStatus
import cgi_server
from importlib import reload
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def get_parse_headers(headers):
    parse_headers = {}

    for header in headers:
        temp = header.split(': ')
        parse_headers[temp[0]] = temp[1]

    return parse_headers


def receive_client_request(client_socket):
    totaldata = b''
    request = ''
    headers = ''
    body = ''

    while True:
        data = client_socket.recv(BUFFER_SIZE)
        totaldata += data
        if len(data) < BUFFER_SIZE:
            break

    totaldata = totaldata.decode()
    split_data = totaldata.split('\r\n')
    request = split_data[0]
    headers = split_data[1:len(split_data)-2]

    if 'POST' in request:
        body = split_data[len(split_data)-1]

    headers = get_parse_headers(headers)

    return request, headers, body


def check_client_request(request):
    if (request == ''):
        print('Request is empty')
        return False, str(HTTPStatus.BAD_REQUEST)

    allowed_paths = {'/', '/css/main.css', '/css/login.css', '/script.js',
                     '/coronadata.json', '/favicon.ico', '/imgs/img_avatar_login.png', '/card'}
    allowed_methods = {'GET', 'POST'}

    request_type, path, protocol_ver = request.split(' ')  # GET URL HTTP/1.1

    if request_type in allowed_methods and path in allowed_paths:
        if float(protocol_ver.split('/')[1]) < 1.1:
            return False, str(HTTPStatus.UPGRADE_REQUIRED)

        return True, str(HTTPStatus.OK)

    else:
        return False, str(HTTPStatus.NOT_FOUND)


def send_response_to_client(response, client_socket):
    client_socket.send(response)


def on_new_client(client_socket, addr):
    client_socket.settimeout(DEFAULT_TIMEOUT)
    print("{} new thread, client ip: {}".format(
        datetime.now(), addr[0]+':'+str(addr[1])))

    try:
        while True:
            if cgi_server.is_bad_ip(client_socket, addr):
                print("{} unknown ip, client ip: {}, reason: {}".format(
                    datetime.now(), addr[0]+':'+str(addr[1]), 'Bad IP'))
                break

            request, request_headers, request_body = receive_client_request(
                client_socket)
            print(request)
            valid, error_msg = check_client_request(request)
            if valid:
                print("{} valid request, client ip: {}".format(
                    datetime.now(), addr[0]+':'+str(addr[1])))

                response_command, response_headers, response_body = cgi_server.handle_client_request(
                    request, request_headers, request_body)

                response = response_command + response_headers + response_body
                send_response_to_client(response, client_socket)
                print("{} sent response, client ip: {}".format(
                    datetime.now(), addr[0]+':'+str(addr[1])))
            else:
                send_response_to_client(error_msg.encode(), client_socket)
                print("{} thread closed, client ip: {}, reason: {}".format(
                    datetime.now(), addr[0]+':'+str(addr[1]), error_msg))
                client_socket.close()
                break

            client_socket.close()
            print("{} thread closed, client ip: {}, reason: {}".format(
                datetime.now(), addr[0]+':'+str(addr[1]), 'Request Ended'))
            break

    except socket.timeout:
        print("{} thread closed, client ip: {}, reason: {}".format(
            datetime.now(), addr[0]+':'+str(addr[1]), 'Socket Timed Out'))

    except Exception as e:
        tb = sys.exc_info()[2]
        lineno = tb.tb_lineno
        client_socket.send(str(HTTPStatus.INTERNAL_SERVER_ERROR).encode())
        print("{} thread closed, client ip: {}, reason: {}, line of error: {}".format(
            datetime.now(), addr[0]+':'+str(addr[1]), e, lineno))


class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.split('\\')[1] == 'cgi_server.py':
            print('Reloaded ' + event.src_path.split('\\')[1])
            try:
                reload(cgi_server)
            except SyntaxError:
                print('Syntax error in ' + event.src_path.split('\\')[1])


def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((IP, PORT))
    server_socket.listen(MAX_LISTEN)

    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(
        event_handler, path=r'HTTP & CGI Servers', recursive=False)
    observer.start()

    while True:
        client_socket, address = server_socket.accept()

        try:
            t = threading.Thread(target=on_new_client,
                                 args=(client_socket, address))
            t.start()
        except Exception as e:
            client_socket.send(HTTPStatus.INTERNAL_SERVER_ERROR)
            print("{} couldn't start thread, client ip: {}, reason: {}".format(
                datetime.now(), address[0]+':'+str(address[1]), e))
            raise


if __name__ == "__main__":
    main()
