
class WebViewModel:
    values = {
        "android.webkit.WebView": [
            "addJavascriptInterface",
            "loadUrl",
            "loadData",
            "loadDataWithBaseURL"
        ]
    }


class WebViewModule(object):
    def __init__(self):
        self.name = "webview"
        self.model = WebViewModel()
