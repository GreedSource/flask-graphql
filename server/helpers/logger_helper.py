import logging


class LoggerHelper:
    # Códigos ANSI para colores
    RESET = "\033[0m"
    COLORS = {
        "DEBUG": "\033[90m",  # Gris oscuro
        "INFO": "\033[94m",  # Azul claro
        "WARNING": "\033[93m",  # Amarillo
        "ERROR": "\033[91m",  # Rojo
        "SUCCESS": "\033[92m",  # Verde
    }

    SUCCESS_LEVEL = 25
    logging.addLevelName(SUCCESS_LEVEL, "SUCCESS")

    @staticmethod
    def _add_success_method():
        def success(self, message, *args, **kwargs):
            if self.isEnabledFor(LoggerHelper.SUCCESS_LEVEL):
                self._log(LoggerHelper.SUCCESS_LEVEL, message, args, **kwargs)

        logging.Logger.success = success

    _logger = None  # instancia única

    @staticmethod
    def _get_logger():
        if LoggerHelper._logger is None:
            logger = logging.getLogger("LoggerHelper")
            logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)

            formatter = LoggerHelper.ColoredFormatter(
                "[%(asctime)s] [%(levelname)s]: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            ch.setFormatter(formatter)

            logger.addHandler(ch)
            LoggerHelper._logger = logger
        return LoggerHelper._logger

    class ColoredFormatter(logging.Formatter):
        def format(self, record):
            levelname = record.levelname
            color = LoggerHelper.COLORS.get(levelname, LoggerHelper.RESET)
            message = super().format(record)
            return f"{color}{message}{LoggerHelper.RESET}"

    @staticmethod
    def debug(msg: str, *args, **kwargs):
        LoggerHelper._get_logger().debug(msg, *args, **kwargs)

    @staticmethod
    def info(msg: str, *args, **kwargs):
        LoggerHelper._get_logger().info(msg, *args, **kwargs)

    @staticmethod
    def warning(msg: str, *args, **kwargs):
        LoggerHelper._get_logger().warning(msg, *args, **kwargs)

    @staticmethod
    def error(msg: str, *args, **kwargs):
        LoggerHelper._get_logger().error(msg, *args, **kwargs)

    @staticmethod
    def success(msg: str, *args, **kwargs):
        LoggerHelper._get_logger().success(msg, *args, **kwargs)


# Registrar método success en logging.Logger
LoggerHelper._add_success_method()
