#!/usr/bin/env python3
"""
Оптимизированный HTTP/HTTPS→SOCKS5 прокси для Google Gemini API
"""

import sys
import socket
import select
import socks
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

SOCKS5_HOST = "127.0.0.1"
SOCKS5_PORT = 12334
HTTP_PORT = 8888
TIMEOUT = 60  # Увеличенный таймаут


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Многопоточный HTTP сервер для обработки параллельных запросов"""

    daemon_threads = True
    allow_reuse_address = True


class OptimizedProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = TIMEOUT

    def log_message(self, format, *args):
        """Минимальное логирование для производительности"""
        if "CONNECT" in format or self.command == "CONNECT":
            print(f"🔐 CONNECT {args[0]}")
        else:
            print(f"📡 {self.command} {args[0]}")

    def do_CONNECT(self):
        """Оптимизированная обработка HTTPS CONNECT"""
        try:
            address = self.path.split(":", 1)
            host = address[0]
            port = int(address[1]) if len(address) == 2 else 443

            # Создаём SOCKS5 соединение с таймаутом
            remote = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            remote.settimeout(TIMEOUT)
            remote.set_proxy(socks.SOCKS5, SOCKS5_HOST, SOCKS5_PORT)

            try:
                remote.connect((host, port))
            except Exception as e:
                print(f"❌ Failed to connect to {host}:{port} via SOCKS5: {e}")
                self.send_error(502, f"Connection failed: {str(e)}")
                return

            # Отправляем успешный ответ СРАЗУ
            self.send_response_only(200)
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            # Flush буфера чтобы клиент сразу получил ответ
            self.wfile.flush()

            # Туннелируем данные
            self._tunnel_data(self.connection, remote)

        except Exception as e:
            print(f"❌ CONNECT Error: {e}")
            try:
                self.send_error(502, f"Proxy Error: {str(e)}")
            except Exception:
                pass

    def _tunnel_data(self, client, server):
        """Оптимизированное двунаправленное туннелирование"""
        client.setblocking(False)
        server.setblocking(False)

        sockets = [client, server]

        try:
            while True:
                ready_read, _, errors = select.select(sockets, [], sockets, TIMEOUT)

                if errors:
                    break

                if not ready_read:
                    # Timeout - закрываем соединение
                    break

                for sock in ready_read:
                    try:
                        data = sock.recv(
                            32768
                        )  # Увеличенный буфер для производительности
                        if not data:
                            return

                        # Определяем целевой socket
                        target = server if sock is client else client
                        target.sendall(data)

                    except (ConnectionResetError, BrokenPipeError, OSError):
                        return
                    except Exception as e:
                        print(f"❌ Tunnel error: {e}")
                        return

        except Exception as e:
            print(f"❌ Select error: {e}")
        finally:
            try:
                server.close()
            except Exception:
                pass

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def do_PUT(self):
        self._handle_request()

    def do_DELETE(self):
        self._handle_request()

    def do_HEAD(self):
        self._handle_request()

    def _handle_request(self):
        """Обработка обычных HTTP запросов (не используется для HTTPS)"""
        try:
            self.send_error(400, "Use HTTPS/CONNECT for this proxy")
        except Exception:
            pass


if __name__ == "__main__":
    try:
        print("🚀 Оптимизированный HTTP/HTTPS→SOCKS5 прокси")
        print(f"   Listening: http://127.0.0.1:{HTTP_PORT}")
        print(f"   Upstream: SOCKS5://{SOCKS5_HOST}:{SOCKS5_PORT}")
        print(f"   Timeout: {TIMEOUT}s")
        print("   Threading: ✅ (параллельные запросы)")
        print("   Нажмите Ctrl+C для остановки\n")

        server = ThreadedHTTPServer(("127.0.0.1", HTTP_PORT), OptimizedProxyHandler)
        server.serve_forever()

    except KeyboardInterrupt:
        print("\n👋 Прокси остановлен")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)
