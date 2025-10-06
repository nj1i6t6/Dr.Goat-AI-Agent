"""簡易背景任務 Worker 啟動腳本"""
from app import create_app
from app.simple_queue import SimpleWorker


def main():
    app = create_app()
    with app.app_context():
        queue = app.extensions['rq_queue']
        worker = SimpleWorker(queue)
        worker.work()


if __name__ == '__main__':
    main()
