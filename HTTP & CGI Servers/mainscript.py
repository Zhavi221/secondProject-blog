from importlib import reload
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import http_server

http_temp = http_server

class MyHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.src_path.split('\\')[1] == 'http_server.py':
            print('Reloaded ' + event.src_path.split('\\')[1])
            try:
                reload(http_server)
            except SyntaxError:
                print('Syntax error in ' + event.src_path.split('\\')[1])
            except:
                raise

if __name__ == "__main__":
    event_handler = MyHandler()
    observer = Observer()
    observer.schedule(event_handler, path=r'HTTP & CGI Servers', recursive=False)
    observer.start()

    http_server.main()
    