import unittest

from timefolio_server import TimeETFTableParser


class TimeETFTableParserTests(unittest.TestCase):
    def test_extracts_required_constituent_fields(self):
        html = '''
        <html><body>
          <table>
            <thead><tr><th>기타</th><th>종목코드</th><th>종목명</th><th>수량</th><th>비중</th></tr></thead>
            <tbody>
              <tr><td>x</td><td>NVDA US EQUITY</td><td>NVIDIA</td><td>1,200</td><td>3.42%</td></tr>
              <tr><td>x</td><td>AAPL US EQUITY</td><td>APPLE</td><td>500</td><td>2.10%</td></tr>
            </tbody>
          </table>
        </body></html>
        '''

        parser = TimeETFTableParser()
        parser.feed(html)
        items = parser.extract_items()

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["code"], "NVDA")
        self.assertEqual(items[0]["name"], "NVIDIA")
        self.assertEqual(items[0]["qty"], 1200.0)
        self.assertEqual(items[0]["weight"], 3.42)



    def test_health_endpoint_returns_ok(self):
        from http.server import ThreadingHTTPServer
        from threading import Thread
        from urllib.request import urlopen

        from timefolio_server import Handler

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlopen(f"http://127.0.0.1:{server.server_port}/api/health", timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get_content_type(), "application/json")
                self.assertEqual(response.read().decode("utf-8"), '{"status": "ok"}')
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()

    def test_returns_empty_for_non_constituent_table(self):
        parser = TimeETFTableParser()
        parser.feed('<table><tr><th>foo</th><th>bar</th></tr><tr><td>1</td><td>2</td></tr></table>')
        self.assertEqual(parser.extract_items(), [])


if __name__ == "__main__":
    unittest.main()
