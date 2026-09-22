import os
import sys

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
INDEX = os.path.join(FRONTEND_DIR, "index.html")


def main():
    try:
        import webview
    except ImportError:
        print("pywebview is not installed. Run: python -m pip install pywebview")
        return 1

    if not os.path.isfile(INDEX):
        print("Frontend entry not found: {0}".format(INDEX))
        return 1

    kwargs = {}
    try:
        from backend_api import BackendAPI
        kwargs["js_api"] = BackendAPI()
        print("backend bridge attached")
    except Exception as error:
        print("backend bridge unavailable: {0}".format(error))

    webview.create_window(
        "صلاة وسكون — Phase 4",
        INDEX,
        width=900,
        height=760,
        min_size=(640, 520),
        **kwargs
    )
    webview.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())