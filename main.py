from caaas import app
from caaas.cleanup_thread import start_cleanup_thread


def main():
    start_cleanup_thread()
    app.debug = True
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.run(host="0.0.0.0")

if __name__ == "__main__":
    main()
