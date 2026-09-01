from .db_initializer import DBInitializer
from .service import *
from collections import deque

from ..logger import Logger
from PySide6.QtCore import QCoreApplication, QObject, QThread, QMutex, QWaitCondition, Signal
from PySide6.QtSql import QSqlDatabase


class SqlRequest:
    """ Sql request """

    def __init__(self, service: str, method: str, slot=None, params: dict = None):
        self.service = service
        self.method = method
        self.slot = slot
        self.params = params or {}


class SqlResponse:
    """ Sql response """

    def __init__(self, data, slot):
        self.slot = slot
        self.data = data


class SqlSignalBus(QObject):
    """ Sql Signal bus """

    fetchDataSig = Signal(SqlRequest)
    dataFetched = Signal(SqlResponse)


sqlSignalBus = SqlSignalBus()


def sqlRequest(service: str, method: str, slot=None, **params):
    """ query sql from database """
    request = SqlRequest(service, method, slot, params)
    sqlSignalBus.fetchDataSig.emit(request)



class Database(QObject):
    """ Database """

    def __init__(self, db: QSqlDatabase = None, parent=None):
        """
        Parameters
        ----------
        directories: List[str]
            audio directories

        db: QDataBase
            database to be used

        watch: bool
            whether to monitor audio directories

        parent:
            parent instance
        """
        super().__init__(parent=parent)
        self.taskService = TaskService(db)

    def setDatabase(self, db: QSqlDatabase):
        """ set the database to be used """
        self.taskService.taskDao.setDatabase(db)



class DatabaseThread(QThread):
    """ Database thread """

    def __init__(self, db: QSqlDatabase = None, parent=None):
        """
        Parameters
        ----------
        directories: List[str]
            audio directories

        db: QDataBase
            database to be used

        watch: bool
            whether to monitor audio directories

        parent:
            parent instance
        """
        super().__init__(parent=parent)
        self.logger = Logger("database")
        self.database = Database(db, self)
        self.tasks = deque()
        self._mutex = QMutex()
        self._hasTask = QWaitCondition()
        self._shutdown = False

        sqlSignalBus.fetchDataSig.connect(self.onFetchData)
        app = QCoreApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.shutdown)
        self.start()

    def run(self):
        while True:
            self._mutex.lock()

            while not self.tasks and not self._shutdown:
                self._hasTask.wait(self._mutex)

            if not self.tasks:
                self._mutex.unlock()
                break

            task, request = self.tasks.popleft()
            self._mutex.unlock()

            try:
                result = task(**request.params)
                sqlSignalBus.dataFetched.emit(SqlResponse(result, request.slot))
            except Exception:
                self.logger.error(f"database task `{request.service}.{request.method}` failed", exc_info=True)

    def onFetchData(self, request: SqlRequest):
        self._mutex.lock()

        if self._shutdown:
            self._mutex.unlock()
            return

        service = getattr(self.database, request.service)
        task = getattr(service, request.method)
        self.tasks.append((task, request))
        self._mutex.unlock()
        self._hasTask.wakeAll()

    def shutdown(self):
        """ stop the database thread after all pending tasks have been processed """
        self._mutex.lock()
        if self._shutdown:
            self._mutex.unlock()
            self.wait()
            return
        self._shutdown = True
        self._mutex.unlock()
        self._hasTask.wakeAll()
        self.wait()

    def __del__(self):
        try:
            self.shutdown()
        except RuntimeError:
            pass