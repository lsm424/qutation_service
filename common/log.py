import loguru

loguru.logger.add("./quotation.log", level="INFO", encoding="utf-8", retention="5 days", rotation="1 day", enqueue=True)
logger = loguru.logger