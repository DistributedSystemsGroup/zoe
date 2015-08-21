import asyncio
import logging
import time
import threading
from rpyc.utils.server import UDPRegistryClient, AuthenticationError, Connection, Channel, SocketStream


class RPyCAsyncIOServer:
    """AsyncIO RpyC server implementation

    :param service: the :class:`service <service.Service>` to expose
    :param hostname: the host to bind to. Default is IPADDR_ANY, but you may
                     want to restrict it only to ``localhost`` in some setups
    :param ipv6: whether to create an IPv6 or IPv4 socket. The default is IPv4
    :param port: the TCP port to bind to
    :param backlog: the socket's backlog (passed to ``listen()``)
    :param reuse_addr: whether or not to create the socket with the ``SO_REUSEADDR`` option set.
    :param authenticator: the :ref:`api-authenticators` to use. If ``None``, no authentication
                          is performed.
    :param registrar: the :class:`registrar <rpyc.utils.registry.RegistryClient>` to use.
                          If ``None``, a default :class:`rpyc.utils.registry.UDPRegistryClient`
                          will be used
    :param auto_register: whether or not to register using the *registrar*. By default, the
                          server will attempt to register only if a registrar was explicitly given.
    :param protocol_config: the :data:`configuration dictionary <rpyc.core.protocol.DEFAULT_CONFIG>`
                            that is passed to the RPyC connection
    :param logger: the ``logger`` to use (of the built-in ``logging`` module). If ``None``, a
                   default logger will be created.
    :param listener_timeout: the timeout of the listener socket; set to ``None`` to disable (e.g.
                             on embedded platforms with limited battery)
    """

    def __init__(self, service, hostname="", ipv6=False, port=0,
            backlog=10, reuse_addr=True, authenticator=None, registrar=None,
            auto_register=None, protocol_config=None, logger=None, listener_timeout=0.5):

        if not protocol_config:
            protocol_config = {}

        self.service = service
        self.authenticator = authenticator
        self.backlog = backlog
        if auto_register is None:
            self.auto_register = bool(registrar)
        else:
            self.auto_register = auto_register
        self.protocol_config = protocol_config

        self.hostname = hostname
        self.port = port

        if logger is None:
            logger = logging.getLogger("%s/%d" % (self.service.get_service_name(), self.port))
        self.logger = logger
        if "logger" not in self.protocol_config:
            self.protocol_config["logger"] = self.logger
        if registrar is None:
            registrar = UDPRegistryClient(logger = self.logger)
        self.registrar = registrar

        # The asyncio Server object
        self.server = None

        # Unused parameters
        self.ipv6 = ipv6
        self.reuse_addr = reuse_addr
        self.listener_timeout = listener_timeout

    def close(self):
        """Closes (terminates) the server and all of its clients. If applicable,
        also unregisters from the registry server"""
        if self.auto_register:
            try:
                self.registrar.unregister(self.port)
            except Exception:
                self.logger.exception("error unregistering services")

    def fileno(self):
        """returns the listener socket's file descriptor"""
        return self.server.sockets[0]

    def _accept_method(self, reader, writer):
        self._authenticate_and_serve_client(reader, writer)

    def _authenticate_and_serve_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        if self.authenticator:
            addrinfo = writer.transport.get_extra_info("peername")
            h = addrinfo[0]
            p = addrinfo[1]
            try:
                credentials = self.authenticator(reader, writer)
            except AuthenticationError:
                self.logger.info("[%s]:%s failed to authenticate, rejecting connection", h, p)
                return
            else:
                self.logger.info("[%s]:%s authenticated successfully", h, p)
        else:
            credentials = None

        try:
            self._serve_client(reader, writer, credentials)
        except Exception:
            self.logger.exception("client connection terminated abruptly")
            raise

        writer.close()

    def _serve_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, credentials):
        addrinfo = writer.transport.get_extra_info("peername")
        h = addrinfo[0]
        p = addrinfo[1]
        sockname = writer.transport.get_extra_info("sockname")
        sock = writer.transport.get_extra_info("socket")
        if credentials:
            self.logger.info("welcome [%s]:%s (%r)", h, p, credentials)
        else:
            self.logger.info("welcome [%s]:%s", h, p)
        try:
            config = dict(self.protocol_config,
                          credentials=credentials,
                          endpoints=(sockname, addrinfo),
                          logger=self.logger)
            conn = Connection(self.service,
                              Channel(SocketStream(sock)),
                              config=config,
                              _lazy=True)
            conn._init_service()
            conn.serve_all()
        finally:
            self.logger.info("goodbye [%s]:%s", h, p)

    def _bg_register(self):
        interval = self.registrar.REREGISTER_INTERVAL
        self.logger.info("started background auto-register thread (interval = %s)", interval)
        tnext = 0
        while True:
            t = time.time()
            if t >= tnext:
                did_register = False
                aliases = self.service.get_service_aliases()
                try:
                    did_register = self.registrar.register(aliases, self.port, interface=self.hostname)
                except Exception:
                    self.logger.exception("error registering services")

                # If registration worked out, retry to register again after
                # interval time. Otherwise, try to register soon again.
                if did_register:
                    tnext = t + interval
                else:
                    self.logger.info("registering services did not work - retry")

            time.sleep(1)

    def start(self):
        """Starts the server. Use :meth:`close` to stop"""
        loop = asyncio.get_event_loop()
        coro = asyncio.start_server(self._accept_method, self.hostname, self.port, loop=loop, backlog=self.backlog)
        self.server = loop.run_until_complete(coro)

        self.logger.info("server started on [%s]:%s", self.hostname, self.port)
        if self.auto_register:
            t = threading.Thread(target=self._bg_register)
            t.setDaemon(True)
            t.start()


