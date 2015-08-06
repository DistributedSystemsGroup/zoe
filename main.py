from caaas import app


def main():
    app.debug = True
    app.run(host="0.0.0.0")

if __name__ == "__main__":
    main()
